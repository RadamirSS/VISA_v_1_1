from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

from bot.models import DocumentFile
from bot.repositories.documents import DocumentRepository


ALLOWED_MIME_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "application/pdf",
    }
)


class DocumentStorageService:
    def __init__(
        self,
        *,
        repository: DocumentRepository,
        storage_dir: Path,
        max_file_mb: int,
        enabled: bool,
    ) -> None:
        self._repository = repository
        self._storage_dir = storage_dir
        self._max_bytes = max_file_mb * 1024 * 1024
        self._enabled = enabled

    @property
    def enabled(self) -> bool:
        return self._enabled

    def validate_upload(self, *, filename: str, content_type: str | None, size_bytes: int) -> str:
        if not self._enabled:
            raise ValueError("Document uploads are disabled")
        if size_bytes <= 0:
            raise ValueError("Empty file")
        if size_bytes > self._max_bytes:
            raise ValueError(f"File exceeds maximum size of {self._max_bytes // (1024 * 1024)} MB")

        mime_type = content_type or mimetypes.guess_type(filename)[0] or ""
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValueError("Unsupported file type")
        return mime_type

    def save_upload(
        self,
        *,
        case_id: str,
        document_item_id: str,
        uploaded_by: str,
        filename: str,
        content_type: str | None,
        content: BinaryIO,
        size_bytes: int,
        applicant_id: str | None = None,
    ) -> DocumentFile:
        mime_type = self.validate_upload(filename=filename, content_type=content_type, size_bytes=size_bytes)
        file_id = str(uuid4())
        target_dir = self._storage_dir / case_id / document_item_id
        target_dir.mkdir(parents=True, exist_ok=True)
        storage_path = target_dir / file_id
        with storage_path.open("wb") as handle:
            handle.write(content.read())

        return self._repository.save_file_metadata(
            document_item_id=document_item_id,
            case_id=case_id,
            uploaded_by=uploaded_by,
            original_filename=Path(filename).name,
            storage_path=str(storage_path),
            mime_type=mime_type,
            size_bytes=size_bytes,
            applicant_id=applicant_id,
        )

    def open_file(self, document_file: DocumentFile) -> Path:
        path = Path(document_file.storage_path)
        if not path.exists():
            raise FileNotFoundError("Stored file not found")
        return path
