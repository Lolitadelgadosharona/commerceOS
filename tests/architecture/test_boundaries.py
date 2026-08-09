import ast
from pathlib import Path

DOMAIN_NAMES = {
    "intelligence",
    "decision",
    "build",
    "growth",
    "operations",
    "finance",
    "learning",
    "governance",
}


def test_domains_do_not_import_other_domain_internals() -> None:
    root = Path("packages/backend/commerce_os")
    violations: list[str] = []
    for domain in DOMAIN_NAMES:
        for path in (root / domain).rglob("*.py"):
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    parts = node.module.split(".")
                    if len(parts) >= 2 and parts[0] == "commerce_os":
                        target = parts[1]
                        if target in DOMAIN_NAMES and target != domain:
                            violations.append(f"{path}: imports {node.module}")
    assert violations == []
