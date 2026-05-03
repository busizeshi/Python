import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^name:\s*([a-z0-9-]{1,64})\s*$")
DESC_RE = re.compile(r"^description:\s*(.+)\s*$")


def validate_skill(skill_dir: Path) -> list[str]:
    errors = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        return [f"Missing file: {skill_md}"]

    text = skill_md.read_text(encoding="utf-8").lstrip("\ufeff")
    if not text.startswith("---"):
        errors.append("SKILL.md must start with YAML frontmatter")
        return errors

    parts = text.split("---", 2)
    if len(parts) < 3:
        errors.append("Invalid frontmatter block")
        return errors

    fm = parts[1].splitlines()
    if not any(NAME_RE.match(line.strip()) for line in fm):
        errors.append("Frontmatter missing valid name")
    if not any(DESC_RE.match(line.strip()) for line in fm):
        errors.append("Frontmatter missing description")

    if (skill_dir / "agents" / "openai.yaml").exists() is False:
        errors.append("Missing agents/openai.yaml")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python tools/quick_validate.py <path-to-skill>")
        return 2

    path = Path(sys.argv[1])
    errors = validate_skill(path)
    if errors:
        print("Validation failed:")
        for e in errors:
            print(f"- {e}")
        return 1

    print(f"Validation passed: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
