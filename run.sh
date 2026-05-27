#!/bin/bash
set -e

cd "$(dirname "$0")"

PYTHON_BIN="python"

if [ -x .venv/bin/python ]; then
    PYTHON_BIN=".venv/bin/python"
elif [ -x venv/bin/python ]; then
    PYTHON_BIN="venv/bin/python"
fi

if [ -f requirements.txt ]; then
    if ! "$PYTHON_BIN" - <<'PY'
import re
import sys
from pathlib import Path
from importlib.metadata import PackageNotFoundError, version

for raw_line in Path("requirements.txt").read_text(encoding="utf-8").splitlines():
    line = raw_line.strip()
    if not line or line.startswith("#"):
        continue

    package = re.split(r"[<>=!~\[]", line, maxsplit=1)[0].strip()
    if not package:
        continue

    try:
        version(package)
    except PackageNotFoundError:
        sys.exit(1)

sys.exit(0)
PY
    then
        "$PYTHON_BIN" -m pip install -r requirements.txt
    fi
fi

"$PYTHON_BIN" newscollector/newscollector.py
