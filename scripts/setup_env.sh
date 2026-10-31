#!/usr/bin/env bash
# Copyright (C) 2020 Pridhvi Patagarla
#
# SovereignAI is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 3 of the License.
#
# SovereignAI is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SovereignAI.  If not, see <https://www.gnu.org/licenses/>.
#
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
