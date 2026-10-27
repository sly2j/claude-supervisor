"""CHANGELOG.md must have an entry for the major version in VERSION (CLAUDE.md)."""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_changelog_has_current_major():
    major = (REPO_ROOT / "VERSION").read_text().strip().split(".")[0]
    changelog = (REPO_ROOT / "CHANGELOG.md").read_text()
    assert re.search(rf"^- \*\*v{major}\*\* \(\d{{4}}-\d{{2}}-\d{{2}}\):", changelog, re.M), \
        f"CHANGELOG.md has no '- **v{major}** (YYYY-MM-DD): ...' entry"
