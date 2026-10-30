# Python development environment

Created on **29 October 2026** for the initial SovereignAI harness, data contracts, and graph adapter work. The development interpreter is **CPython 3.11.18**, running natively on this machine's Apple Silicon (`arm64`). The environment uses the existing **uv 0.13.5** installation to manage dependencies.

## Activate and use

From the SovereignAI project directory:

```sh
source .venv/bin/activate
python --version
```

Expected version: `Python 3.11.18`. Run `deactivate` to leave the environment. Activation affects the current shell only. In an editor, select `.venv/bin/python` as this project's interpreter.

You can also use the environment without activation:

```sh
uv run --locked python --version
uv run --locked pytest --version
uv run --locked ruff --version
```

There is no application entry point yet. This setup prepares implementation dependencies; it does not start a learner or graph database.

## Installed foundation libraries

| Library | Pinned version | Purpose |
|---|---|---|
| Neo4j Python driver | 6.4.0 | Official driver for the planned graph adapter |
| Pydantic | 2.14.1 | Explicit, validated data contracts for the Python harness |
| pytest | 9.1.1 | Test runner for upcoming implementation |
| Hypothesis | 6.169.2 | Property-based checks for Unicode sequences, serialization, and invariants |
| Ruff | 0.17.0 | Python linting and formatting |
| OpenAI SDK | 3.31.0 | Development assistance only |
| python-dotenv | 1.2.4 | Read the authorized external credential file without copying it |

pytest, Hypothesis, Ruff, the OpenAI SDK and python-dotenv are development dependencies. Python's standard library supplies JSON, hashing, SQLite, archives, logging, and process management. Add further libraries when an implemented component needs them; this limits the initial compatibility surface.

The [project configuration](../pyproject.toml) pins all seven direct dependencies. [uv.lock](../uv.lock) records the complete resolved dependency graph and distribution hashes. After the authorized development API setup on 30 October, the macOS environment contains 25 installed distributions; the portable lock also includes conditional dependencies for other supported platforms. The [development-assistance guide](DEVELOPMENT_ASSISTANCE.md) defines the API boundary.

The [environment receipt](../manifests/python-environment.json) records the installed package versions, runtime/build details, Unicode versions, and configuration hashes at setup time. Regenerate this record after a deliberate environment update; it is a receipt, not a replacement for the lockfile.

## Stability and update policy

- Use only final releases: prereleases are disabled.
- The initial library resolution uses a fixed cutoff of **15 October 2026 at 00:00 UTC**, allowing at least two weeks before the setup date. Release age is one selection measure, not a guarantee of reliability.
- Pin direct dependencies exactly and retain the full lockfile. Ordinary setup uses `--locked` and fails if project declarations and the lock disagree.
- Install available wheels with `--no-build` during setup. The current platform required no local source builds.
- Review dependency updates explicitly, rerun the relevant tests, and record any behavior or compatibility changes. Advance the cutoff deliberately when reviewing newer releases; do not let it prevent a needed security update.
- Keep Python on the requested 3.11 series. `.python-version` pins the exact runtime; `requires-python` excludes 3.12 and later. Python 3.11's documented security-support window ends in October 2027, so review the runtime choice before then. [Python 3.11.18 release notes](https://www.python.org/downloads/release/python-31118/).

Python 3.11.18 is a security release, so the library-age cutoff does not apply to the interpreter. The binaries are supplied by Astral's `python-build-standalone`, the distribution used by uv. The metadata URL is pinned to uv's 0.13.6 release because the installed uv 0.13.5 predates this Python patch. [uv Python installation documentation](https://docs.astral.sh/uv/guides/install-python/).

## Recreate the environment

Use uv `>=0.13.5,<0.14`, the range declared in the project configuration, then run:

```sh
bash scripts/setup_env.sh
```

The script locates the project independently of the calling directory, installs the pinned interpreter if necessary, synchronizes the locked dependencies including the development group, and checks package compatibility. Downloads require internet access when the necessary artifacts are not already available.

Local directories are:

```text
.python/      uv-managed CPython installation
.venv/        project virtual environment
.cache/uv/    download and package cache
```

These directories are ignored by Git. Keep `.python-version`, `pyproject.toml`, `uv.lock`, and `scripts/setup_env.sh` with the project. Recreate virtual environments after moving the project to another location; their interpreter paths are not portable. The script does not register global Python executables or change shell startup files.

## Unicode 18 integration

Python 3.11.18's built-in `unicodedata` reports **Unicode 14.0.0**. Python can still carry valid Unicode scalar values through UTF-8 strings, but built-in character properties, normalization tables, and character classifications must not be used as Unicode 18 authorities.

The project's [downloaded Unicode 18.0.0 data](../data/unicode/18.0.0/README.md) remains the pinned reference for the future symbol registry and tokenizer. Unicode conformance testing is a separate implementation milestone; installing Python does not fulfill it.

## Setup validation

The following checks passed on this machine on 29 October 2026:

- `uv pip check`: all 15 installed distributions have compatible declared dependencies.
- `uv lock --check --offline`: the lockfile matches the project configuration.
- A second run of `scripts/setup_env.sh`: the environment reproduces its locked state without changes.
- Five temporary pytest smoke checks: exact interpreter and isolation; native compression, hashing, TLS-context and SQLite operations; Pydantic strict validation; Neo4j driver construction/closure; and 100 generated scalar-string UTF-8 round trips using Hypothesis.
- Ruff linting of the smoke-check source, plus direct version checks of pytest and Ruff.

The temporary smoke checks were removed after execution. These checks establish that the installed tools work together for these basic operations. They do not measure learner performance, certify Unicode 18 conformance, or test a live Neo4j connection.

On 30 October, after the authorized OpenAI development-tool setup, all **25** installed distributions passed dependency compatibility checks and their declared Python requirements accepted **3.11.18**. All **seven** direct pins matched the installed versions. Offline locked synchronization, key library imports, helper configuration, and Ruff checks passed. The [dependency report](../manifests/dependency-check.json) records versions and Python requirements; the check scope is installed-package compatibility, not a vulnerability audit. The [live API verification](../manifests/development-api-verification.json) records the one bounded request made during setup.
