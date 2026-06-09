from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import Optional
from uuid import uuid4

from bot.database import sqlite_path_from_url
from bot.models import (
    AgencyDocumentStatus,
    ClientDocumentStatus,
    DocumentCategory,
    DocumentFile,
    DocumentFileStatus,
    DocumentItem,
    DocumentSourceType,
)
from bot.services.document_status import (
    build_document_summary_counts,
    validate_agency_ready_status,
    validate_status_for_source,
)
from bot.services.document_templates import get_template, resolve_title


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


class DocumentRepository:
    def __init__(self, database_url: str) -> None:
        self._path = sqlite_path_from_url(database_url)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        return connection

    def _item_from_row(self, row: sqlite3.Row) -> DocumentItem:
        return DocumentItem(
            id=row["id"],
            case_id=row["case_id"],
            applicant_id=row["applicant_id"],
            source_type=row["source_type"],
            category=row["category"],
            title=row["title"],
            description=row["description"],
            status=row["status"],
            required=bool(row["required"]),
            visible_to_client=bool(row["visible_to_client"]),
            requested_by_admin_id=row["requested_by_admin_id"],
            requested_at=row["requested_at"],
            due_date=row["due_date"],
            uploaded_by=row["uploaded_by"],
            uploaded_at=row["uploaded_at"],
            reviewed_by_admin_id=row["reviewed_by_admin_id"],
            reviewed_at=row["reviewed_at"],
            manager_comment=row["manager_comment"],
            client_comment=row["client_comment"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    def _file_from_row(self, row: sqlite3.Row) -> DocumentFile:
        return DocumentFile(
            id=row["id"],
            document_item_id=row["document_item_id"],
            case_id=row["case_id"],
            applicant_id=row["applicant_id"],
            uploaded_by=row["uploaded_by"],
            original_filename=row["original_filename"],
            storage_path=row["storage_path"],
            mime_type=row["mime_type"],
            size_bytes=row["size_bytes"],
            status=row["status"],
            created_at=row["created_at"],
        )

    def create_client_request(
        self,
        case_id: str,
        category: str,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        admin_id: int,
        comment: Optional[str] = None,
        applicant_id: Optional[str] = None,
        required: Optional[bool] = None,
    ) -> DocumentItem:
        template = get_template(category)
        if template is None or template.source_type != DocumentSourceType.CLIENT_REQUIRED.value:
            raise ValueError(f"Unknown client-required category: {category}")

        timestamp = now_iso()
        item = DocumentItem(
            id=str(uuid4()),
            case_id=case_id,
            applicant_id=applicant_id,
            source_type=DocumentSourceType.CLIENT_REQUIRED.value,
            category=category,
            title=title or template.title,
            description=description or template.description,
            status=ClientDocumentStatus.REQUESTED.value,
            required=template.required if required is None else required,
            visible_to_client=True,
            requested_by_admin_id=admin_id,
            requested_at=timestamp,
            manager_comment=comment,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self._insert_item(item)
        return item

    def create_agency_item(
        self,
        case_id: str,
        category: str,
        *,
        title: Optional[str] = None,
        description: Optional[str] = None,
        admin_id: int,
        applicant_id: Optional[str] = None,
    ) -> DocumentItem:
        template = get_template(category)
        if template is None or template.source_type != DocumentSourceType.AGENCY_PREPARED.value:
            raise ValueError(f"Unknown agency-prepared category: {category}")

        timestamp = now_iso()
        item = DocumentItem(
            id=str(uuid4()),
            case_id=case_id,
            applicant_id=applicant_id,
            source_type=DocumentSourceType.AGENCY_PREPARED.value,
            category=category,
            title=title or template.title,
            description=description or template.description,
            status=AgencyDocumentStatus.PREPARING_BY_AGENCY.value,
            required=False,
            visible_to_client=True,
            requested_by_admin_id=admin_id,
            requested_at=timestamp,
            created_at=timestamp,
            updated_at=timestamp,
        )
        self._insert_item(item)
        return item

    def create_custom_client_request(
        self,
        case_id: str,
        custom_title: str,
        *,
        admin_id: int,
        comment: Optional[str] = None,
        applicant_id: Optional[str] = None,
    ) -> DocumentItem:
        return self.create_client_request(
            case_id,
            DocumentCategory.OTHER_CLIENT_DOCUMENT.value,
            title=resolve_title(DocumentCategory.OTHER_CLIENT_DOCUMENT.value, custom_title),
            admin_id=admin_id,
            comment=comment,
            applicant_id=applicant_id,
            required=False,
        )

    def create_custom_agency_item(
        self,
        case_id: str,
        custom_title: str,
        *,
        admin_id: int,
        applicant_id: Optional[str] = None,
    ) -> DocumentItem:
        return self.create_agency_item(
            case_id,
            DocumentCategory.OTHER_AGENCY_DOCUMENT.value,
            title=resolve_title(DocumentCategory.OTHER_AGENCY_DOCUMENT.value, custom_title),
            admin_id=admin_id,
            applicant_id=applicant_id,
        )

    def _insert_item(self, item: DocumentItem) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO document_items (
                  id, case_id, applicant_id, source_type, category, title, description,
                  status, required, visible_to_client, requested_by_admin_id, requested_at,
                  due_date, uploaded_by, uploaded_at, reviewed_by_admin_id, reviewed_at,
                  manager_comment, client_comment, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    item.id,
                    item.case_id,
                    item.applicant_id,
                    item.source_type,
                    item.category,
                    item.title,
                    item.description,
                    item.status,
                    int(item.required),
                    int(item.visible_to_client),
                    item.requested_by_admin_id,
                    item.requested_at,
                    item.due_date,
                    item.uploaded_by,
                    item.uploaded_at,
                    item.reviewed_by_admin_id,
                    item.reviewed_at,
                    item.manager_comment,
                    item.client_comment,
                    item.created_at,
                    item.updated_at,
                ),
            )

    def list_by_case(self, case_id: str, *, visible_to_client_only: bool = False) -> list[DocumentItem]:
        query = "SELECT * FROM document_items WHERE case_id = ?"
        params: tuple = (case_id,)
        if visible_to_client_only:
            query += " AND visible_to_client = 1"
        query += " ORDER BY created_at ASC"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [self._item_from_row(row) for row in rows]

    def get_by_id(self, document_id: str) -> Optional[DocumentItem]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM document_items WHERE id = ?",
                (document_id,),
            ).fetchone()
        return self._item_from_row(row) if row else None

    def get_for_case(self, case_id: str, document_id: str) -> Optional[DocumentItem]:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT * FROM document_items WHERE id = ? AND case_id = ?",
                (document_id, case_id),
            ).fetchone()
        return self._item_from_row(row) if row else None

    def update_status(self, document_id: str, status: str, *, admin_id: Optional[int] = None) -> DocumentItem:
        item = self.get_by_id(document_id)
        if item is None:
            raise ValueError("Document not found")
        validate_status_for_source(item.source_type, status)
        if item.source_type == DocumentSourceType.AGENCY_PREPARED.value:
            validate_agency_ready_status(status=status, has_file=self.has_active_file(document_id))
        timestamp = now_iso()
        reviewed_by_admin_id = admin_id
        reviewed_at = timestamp if admin_id is not None else item.reviewed_at
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE document_items
                SET status = ?, reviewed_by_admin_id = ?, reviewed_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (status, reviewed_by_admin_id, reviewed_at, timestamp, document_id),
            )
        updated = self.get_by_id(document_id)
        assert updated is not None
        return updated

    def add_manager_comment(self, document_id: str, comment: str, admin_id: int) -> DocumentItem:
        item = self.get_by_id(document_id)
        if item is None:
            raise ValueError("Document not found")
        timestamp = now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE document_items
                SET manager_comment = ?, reviewed_by_admin_id = ?, reviewed_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (comment.strip(), admin_id, timestamp, timestamp, document_id),
            )
        updated = self.get_by_id(document_id)
        assert updated is not None
        return updated

    def add_client_comment(self, document_id: str, comment: str, uploaded_by: str) -> DocumentItem:
        item = self.get_by_id(document_id)
        if item is None:
            raise ValueError("Document not found")
        timestamp = now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE document_items
                SET client_comment = ?, uploaded_by = ?, updated_at = ?
                WHERE id = ?
                """,
                (comment.strip(), uploaded_by, timestamp, document_id),
            )
        updated = self.get_by_id(document_id)
        assert updated is not None
        return updated

    def mark_uploaded_by_client(self, document_id: str, uploaded_by: str) -> DocumentItem:
        item = self.get_by_id(document_id)
        if item is None:
            raise ValueError("Document not found")
        if item.source_type != DocumentSourceType.CLIENT_REQUIRED.value:
            raise ValueError("Only client-required documents can be uploaded by client")
        if item.status not in {
            ClientDocumentStatus.REQUESTED.value,
            ClientDocumentStatus.REJECTED.value,
        }:
            raise ValueError("Document is not awaiting upload")
        timestamp = now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE document_items
                SET status = ?, uploaded_by = ?, uploaded_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    ClientDocumentStatus.UPLOADED_BY_CLIENT.value,
                    uploaded_by,
                    timestamp,
                    timestamp,
                    document_id,
                ),
            )
        updated = self.get_by_id(document_id)
        assert updated is not None
        return updated

    def mark_insurance_not_available(
        self,
        case_id: str,
        document_id: str,
        comment: str,
        *,
        admin_id: int = 0,
    ) -> tuple[DocumentItem, Optional[DocumentItem]]:
        item = self.get_for_case(case_id, document_id)
        if item is None:
            raise ValueError("Document not found")
        if item.category != DocumentCategory.INSURANCE_OWN.value:
            raise ValueError("Action is only available for client insurance documents")
        timestamp = now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE document_items
                SET status = ?, client_comment = ?, uploaded_by = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    ClientDocumentStatus.NOT_NEEDED.value,
                    comment.strip(),
                    "client",
                    timestamp,
                    document_id,
                ),
            )
        updated = self.get_by_id(document_id)
        assert updated is not None

        existing_agency = [
            doc
            for doc in self.list_by_case(case_id)
            if doc.category == DocumentCategory.INSURANCE_AGENCY_PREPARED.value
            and doc.status != AgencyDocumentStatus.NOT_NEEDED.value
        ]
        agency_item = existing_agency[0] if existing_agency else None
        if agency_item is None:
            agency_item = self.create_agency_item(
                case_id,
                DocumentCategory.INSURANCE_AGENCY_PREPARED.value,
                admin_id=admin_id or item.requested_by_admin_id or 0,
            )
        return updated, agency_item

    def count_summary(self, case_id: str) -> dict[str, int | bool]:
        items = self.list_by_case(case_id, visible_to_client_only=True)
        return build_document_summary_counts(items)

    def save_file_metadata(
        self,
        *,
        document_item_id: str,
        case_id: str,
        uploaded_by: str,
        original_filename: str,
        storage_path: str,
        mime_type: Optional[str],
        size_bytes: Optional[int],
        applicant_id: Optional[str] = None,
    ) -> DocumentFile:
        timestamp = now_iso()
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE document_files
                SET status = ?
                WHERE document_item_id = ? AND status = ?
                """,
                (DocumentFileStatus.REPLACED.value, document_item_id, DocumentFileStatus.ACTIVE.value),
            )
            document_file = DocumentFile(
                id=str(uuid4()),
                document_item_id=document_item_id,
                case_id=case_id,
                applicant_id=applicant_id,
                uploaded_by=uploaded_by,
                original_filename=original_filename,
                storage_path=storage_path,
                mime_type=mime_type,
                size_bytes=size_bytes,
                status=DocumentFileStatus.ACTIVE.value,
                created_at=timestamp,
            )
            connection.execute(
                """
                INSERT INTO document_files (
                  id, document_item_id, case_id, applicant_id, uploaded_by,
                  original_filename, storage_path, mime_type, size_bytes, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    document_file.id,
                    document_file.document_item_id,
                    document_file.case_id,
                    document_file.applicant_id,
                    document_file.uploaded_by,
                    document_file.original_filename,
                    document_file.storage_path,
                    document_file.mime_type,
                    document_file.size_bytes,
                    document_file.status,
                    document_file.created_at,
                ),
            )
        return document_file

    def list_files(self, document_item_id: str) -> list[DocumentFile]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT * FROM document_files
                WHERE document_item_id = ?
                ORDER BY created_at DESC
                """,
                (document_item_id,),
            ).fetchall()
        return [self._file_from_row(row) for row in rows]

    def get_latest_active_file(self, document_item_id: str) -> Optional[DocumentFile]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM document_files
                WHERE document_item_id = ? AND status = ?
                ORDER BY created_at DESC
                LIMIT 1
                """,
                (document_item_id, DocumentFileStatus.ACTIVE.value),
            ).fetchone()
        return self._file_from_row(row) if row else None

    def get_file_for_case(self, case_id: str, document_id: str, file_id: str) -> Optional[DocumentFile]:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT * FROM document_files
                WHERE id = ? AND case_id = ? AND document_item_id = ?
                """,
                (file_id, case_id, document_id),
            ).fetchone()
        return self._file_from_row(row) if row else None

    def mark_agency_ready_after_upload(self, document_id: str, *, admin_id: int) -> DocumentItem:
        item = self.get_by_id(document_id)
        if item is None:
            raise ValueError("Document not found")
        if item.source_type != DocumentSourceType.AGENCY_PREPARED.value:
            raise ValueError("Only agency-prepared documents can receive manager uploads")
        if not self.has_active_file(document_id):
            raise ValueError("Agency file metadata was not saved")
        return self.update_status(document_id, AgencyDocumentStatus.READY_FOR_CLIENT.value, admin_id=admin_id)

    def mark_transferred_separately(self, document_id: str, *, admin_id: int, comment: Optional[str] = None) -> DocumentItem:
        item = self.get_by_id(document_id)
        if item is None:
            raise ValueError("Document not found")
        if item.source_type != DocumentSourceType.AGENCY_PREPARED.value:
            raise ValueError("Only agency-prepared documents can be marked as transferred separately")
        timestamp = now_iso()
        manager_comment = comment or "Документ будет передан менеджером отдельно."
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE document_items
                SET status = ?, manager_comment = ?, reviewed_by_admin_id = ?, reviewed_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    AgencyDocumentStatus.TRANSFERRED_SEPARATELY.value,
                    manager_comment,
                    admin_id,
                    timestamp,
                    timestamp,
                    document_id,
                ),
            )
        updated = self.get_by_id(document_id)
        assert updated is not None
        return updated

    def has_active_file(self, document_item_id: str) -> bool:
        return self.get_latest_active_file(document_item_id) is not None
