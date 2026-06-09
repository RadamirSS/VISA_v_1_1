from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
BOT_ROOT = REPO_ROOT / "apps" / "telegram-bot"

REQUIRED_ENV_VARS = [
    "BOT_TOKEN",
    "BOT_ADMIN_IDS",
    "DATABASE_URL",
    "CLIENT_MINIAPP_URL",
    "MINIAPP_BOT_TOKEN",
    "MINIAPP_ALLOWED_ORIGIN",
    "MINIAPP_DEV_AUTH",
    "DOCUMENT_UPLOADS_ENABLED",
    "DOCUMENT_STORAGE_DIR",
    "DOCUMENT_MAX_FILE_MB",
]

DEPLOYMENT_STORAGE_PHRASES = [
    "stored locally",
    "object storage",
    "encryption-at-rest",
]

PILOT_READINESS_STORAGE_PHRASES = [
    "local file storage",
    "object storage",
    "encryption-at-rest",
]


def _parse_env_keys(content: str) -> set[str]:
    keys: set[str] = set()
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        keys.add(stripped.split("=", 1)[0].strip())
    return keys


def test_env_example_contains_required_pilot_variables() -> None:
    env_example = BOT_ROOT / ".env.example"
    content = env_example.read_text(encoding="utf-8")
    keys = _parse_env_keys(content)

    missing = [name for name in REQUIRED_ENV_VARS if name not in keys]
    assert not missing, f"Missing env vars in .env.example: {missing}"
    assert "secure object storage" in content.lower()


def test_document_storage_path_is_gitignored() -> None:
    gitignore = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "apps/telegram-bot/storage/" in gitignore


def test_deployment_doc_mentions_production_storage_limits() -> None:
    deployment = (REPO_ROOT / "docs" / "DEPLOYMENT.md").read_text(encoding="utf-8").lower()
    for phrase in DEPLOYMENT_STORAGE_PHRASES:
        assert phrase in deployment, f"DEPLOYMENT.md missing phrase: {phrase}"


def test_pilot_readiness_doc_mentions_production_storage_limits() -> None:
    readiness = (REPO_ROOT / "docs" / "PILOT_READINESS.md").read_text(encoding="utf-8").lower()
    for phrase in PILOT_READINESS_STORAGE_PHRASES:
        assert phrase in readiness, f"PILOT_READINESS.md missing phrase: {phrase}"
