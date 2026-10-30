#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$project_root"

if ! command -v uv >/dev/null 2>&1; then
    printf '%s\n' 'Install uv >=0.13.5,<0.14 before running this script. See docs/ENVIRONMENT.md.' >&2
    exit 1
fi

export UV_CACHE_DIR="$project_root/.cache/uv"
export UV_PYTHON_INSTALL_DIR="$project_root/.python"
python_version="$(cat .python-version)"

uv python install "$python_version" --no-bin
uv sync --locked --managed-python --no-build
uv pip check --python .venv/bin/python
.venv/bin/python --version

printf '\n%s\n' 'Environment ready. Activate it with: source .venv/bin/activate'
