from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DOCS = REPO_ROOT / "docs"
README = REPO_ROOT / "README.md"


def test_pilot_release_notes_exists_with_required_sections() -> None:
    path = DOCS / "PILOT_RELEASE_NOTES.md"
    assert path.exists(), "PILOT_RELEASE_NOTES.md is missing"
    content = path.read_text(encoding="utf-8").lower()
    for heading in (
        "what is ready",
        "how to use in closed pilot",
        "known limitations",
        "go / no-go",
        "verification commands",
    ):
        assert heading in content, f"PILOT_RELEASE_NOTES.md missing section: {heading}"


def test_pilot_qa_checklist_references_release_notes_and_trust_tests() -> None:
    content = (DOCS / "PILOT_QA_CHECKLIST.md").read_text(encoding="utf-8")
    assert "PILOT_RELEASE_NOTES.md" in content
    assert "test_trust_copy_safety.py" in content
    assert "Website lead flow" in content
    assert "pnpm typecheck" in content


def test_pilot_readiness_contains_limitations_copy() -> None:
    content = (DOCS / "PILOT_READINESS.md").read_text(encoding="utf-8")
    assert "Сервис помогает" in content
    assert "внешних визовых систем" in content
    assert "консульство" in content


def test_readme_links_pilot_release_notes() -> None:
    content = README.read_text(encoding="utf-8")
    assert "PILOT_RELEASE_NOTES.md" in content
