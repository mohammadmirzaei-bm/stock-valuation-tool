#!/usr/bin/env python3
"""Export the backend OpenAPI schema to ``src/api/openapi.json``.

Runs the ``fastapi`` app from the sibling ``stock_valuation`` package and dumps
its machine-readable schema so ``openapi-typescript`` can generate request and
response types. Kept free of the frontend runtime dependencies.

Usage (from the ``frontend`` directory):

    python3 scripts/gen_openapi.py [output_path]
"""

import json
import sys
from pathlib import Path

# The repository root is the parent of the frontend directory.
REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "src" / "api" / "openapi.json"


def main() -> int:
    from stock_valuation.api.main import app  # imported after path fix-up

    schema = app.openapi()
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(schema, ensure_ascii=False, indent=2, sort_keys=True))
    print(f"Wrote OpenAPI schema ({len(schema.get('paths', {}))} paths) to {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
