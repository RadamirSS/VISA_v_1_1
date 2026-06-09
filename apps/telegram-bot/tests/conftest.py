from __future__ import annotations

import sys
from pathlib import Path

from bot.api import main as api_main
from bot.config import Settings
from bot.database import init_db
from bot.repositories.access_keys import AccessKeyRepository
from bot.repositories.documents import DocumentRepository
from bot.repositories.miniapp import MiniAppRepository
from bot.repositories.users import UserRepository
from bot.services.document_storage import DocumentStorageService


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def build_api_container(
    tmp_path: Path,
    *,
    database_name: str = "test.db",
    uploads_enabled: bool = False,
    miniapp_dev_auth: bool = True,
) -> api_main.Container:
    database_url = f"sqlite+aiosqlite:///{tmp_path / database_name}"
    repo_root = Path(__file__).resolve().parents[3]
    init_db(database_url)
    documents = DocumentRepository(database_url)
    settings = Settings(
        bot_token="",
        bot_admin_ids=[],
        database_url=database_url,
        client_miniapp_url="http://localhost:3001",
        miniapp_bot_token="",
        miniapp_allowed_origin="http://localhost:3001",
        miniapp_dev_auth=miniapp_dev_auth,
        document_uploads_enabled=uploads_enabled,
        document_storage_dir=tmp_path / "storage" / "documents",
        document_max_file_mb=15,
        repo_root=repo_root,
        root_dir=repo_root / "apps" / "telegram-bot",
    )
    api_main._container = api_main.Container(
        settings=settings,
        users=UserRepository(database_url),
        access_keys=AccessKeyRepository(database_url),
        miniapp=MiniAppRepository(database_url, repo_root=repo_root),
        documents=documents,
        document_storage=DocumentStorageService(
            repository=documents,
            storage_dir=settings.document_storage_dir,
            max_file_mb=settings.document_max_file_mb,
            enabled=uploads_enabled,
        ),
    )
    return api_main.get_container()
