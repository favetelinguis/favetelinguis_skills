#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""
Run self-tests for py-skill-creator.

Usage:
    run_self_tests.py
"""

from __future__ import annotations

import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from init_skill import init_skill
from package_skill import package_skill
from validate_skill import validate_skill


VALID_SCRIPT = """#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

print(\"ok\")
"""


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def make_executable(path: Path) -> None:
    path.chmod(0o755)


def build_minimal_skill(base_dir: Path, name: str = "sample-skill") -> Path:
    skill_dir = base_dir / name
    (skill_dir / "scripts").mkdir(parents=True)
    write_text(
        skill_dir / "SKILL.md",
        f"""---
name: {name}
description: >-
  Minimal test skill used to validate the py-skill-creator toolchain.
---

# {name}

Use `uv run scripts/example.py` when validating this fixture.
See [patterns](references/patterns.md).
""",
    )
    write_text(skill_dir / "scripts" / "example.py", VALID_SCRIPT)
    make_executable(skill_dir / "scripts" / "example.py")
    write_text(skill_dir / "references" / "patterns.md", "fixture\n")
    return skill_dir


def test_init_skill() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        created = init_skill(
            "demo-skill",
            root,
            include_example_script=False,
            include_references=True,
            include_assets=True,
        )
        assert_true(created is not None, "init_skill should create the skill")
        assert_true((created / "SKILL.md").exists(), "SKILL.md should exist")
        assert_true((created / "scripts").is_dir(), "scripts/ should exist")
        assert_true(not (created / "scripts" / "example.py").exists(), "example.py should be omitted")
        assert_true((created / "references").is_dir(), "references/ should exist")
        assert_true((created / "assets").is_dir(), "assets/ should exist")


def test_validate_success() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        skill_dir = build_minimal_skill(Path(tmp))
        ok, msg = validate_skill(skill_dir)
        assert_true(ok, f"expected valid skill, got: {msg}")


def test_directory_name_must_match_frontmatter() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        skill_dir = build_minimal_skill(Path(tmp), name="actual-name")
        write_text(
            skill_dir / "SKILL.md",
            """---
name: different-name
description: >-
  Mismatched name for validation.
---

# Broken
""",
        )
        ok, msg = validate_skill(skill_dir)
        assert_true(not ok and "Directory name" in msg, f"expected directory-name error, got: {msg}")


def test_script_metadata_is_required() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        skill_dir = build_minimal_skill(Path(tmp))
        write_text(
            skill_dir / "scripts" / "example.py",
            "#!/usr/bin/env -S uv run\nprint('missing metadata')\n",
        )
        make_executable(skill_dir / "scripts" / "example.py")
        ok, msg = validate_skill(skill_dir)
        assert_true(not ok and "PEP 723" in msg, f"expected metadata error, got: {msg}")


def test_packaging_excludes_junk() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        skill_dir = build_minimal_skill(tmp_path)
        write_text(skill_dir / "scripts" / "__pycache__" / "example.cpython-314.pyc", "junk")
        write_text(skill_dir / ".DS_Store", "junk")
        output_dir = skill_dir
        package_path = package_skill(skill_dir, output_dir)
        assert_true(package_path is not None, "package_skill should succeed")

        with zipfile.ZipFile(package_path) as archive:
            names = set(archive.namelist())

        expected_prefix = f"{skill_dir.name}/"
        assert_true(f"{expected_prefix}SKILL.md" in names, "package should include SKILL.md")
        assert_true(
            f"{expected_prefix}scripts/example.py" in names,
            "package should include the example script",
        )
        assert_true(
            all("__pycache__" not in name for name in names),
            f"package should exclude __pycache__: {sorted(names)}",
        )
        assert_true(
            all(not name.endswith(".pyc") for name in names),
            f"package should exclude .pyc files: {sorted(names)}",
        )
        assert_true(
            all(not name.endswith(".skill") for name in names),
            f"package should not include nested .skill files: {sorted(names)}",
        )


def main() -> None:
    tests = [
        test_init_skill,
        test_validate_success,
        test_directory_name_must_match_frontmatter,
        test_script_metadata_is_required,
        test_packaging_excludes_junk,
    ]

    for test in tests:
        test()
        print(f"PASS {test.__name__}")

    print(f"\nAll {len(tests)} self-tests passed.")


if __name__ == "__main__":
    main()
