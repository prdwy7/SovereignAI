# OpenAI development assistance

Configured on **30 October 2026**. The user authorized reuse of **CodexAPIkey**, identified as Personal / Default project, and explicitly selected **development assistance only; preserve the from-scratch learner**. The key's account labels are user-provided metadata; a successful API request verifies operational access, not those labels independently.

## Scope and supported use

OpenAI can assist with architecture/code review, debugging, test planning, and research planning while developers implement SovereignAI. Outputs are proposals for developers to inspect and verify. Generated code and fixtures need review for undeclared vocabulary, grammatical rules, subject knowledge, or evaluator answers.

For M1.2 the user explicitly requested API-authored implementation and tests, with Codex monitoring and inspection. The existing helper supplied bounded code proposals under `design`, corrections under `debug`, test code under `test-plan` and a final `review`. Codex inspected each response before applying it, requested repairs and ran local verification. This expanded that build's original optional-review allowance; it does not authorize unattended execution or unrestricted API use in future builds. The [M1.2 receipt](../manifests/m1-2-verification.json) records nine requests and 60,566 total tokens.

The learner uses its own declared foundations and experience. External API output is ineligible for teacher seeds, lexical knowledge, training/practice examples, model embeddings, learner responses, authoritative grades, or promotion evidence. The future ingestion/promotion implementation must enforce this distinction; a development-tool label by itself does not implement that future boundary.

Each new build follows the user's [approval workflow](BUILD_WORKFLOW.md). A build proposal states how API assistance will be used. The helper performs a single explicit request and cannot execute suggestions, modify learner state, or start an unattended agent loop.

## Credentials

[config/development_api.toml](../config/development_api.toml) references the existing credential file:

```text
/Users/prdwy/Documents/Codex/2026-10-30/help-me-set-up-openai-developers/.env.local
```

The helper reads `OPENAI_API_KEY` from that file into memory using `python-dotenv` with interpolation disabled. It does not copy the key into this repository or register it in the shell. The specified file is authoritative; an unrelated inherited `OPENAI_API_KEY` does not override it. To intentionally change the file location, set `SOVEREIGNAI_OPENAI_ENV_FILE` to another authorized file path. No key value belongs in an argument, prompt, document, or log.

## Commands

From the project root, check local setup without making an API request:

```sh
uv run --locked python scripts/dev_assistant.py check
```

Submit an explicit UTF-8 development prompt file:

```sh
uv run --locked python scripts/dev_assistant.py request \
  --purpose review --prompt-file path/to/development-prompt.txt
```

The default prompt source is standard input. Available purposes are `design`, `review`, `debug`, `test-plan`, and `research-plan`. Only the supplied text is sent; the helper does not crawl or upload the project. Requests go to the official OpenAI endpoint with `store=False`, a 60-second timeout, and no automatic retries. `store=False` controls response storage and is not a general promise about all service-side retention.

The default model is `gpt-6-luna`; one request can select `gpt-6.1-sol` or `gpt-6-astra` with `--model`. The model catalog identifies Luna for focused cost-sensitive work and Sol/Astra for more demanding work. Actual access depends on the account. There is no automatic model fallback or escalation. [Official model catalog](https://developers.openai.com/api/docs/models).

The default output ceiling is 1,536 tokens, with a hard cap of 4,096. `--max-output-tokens` can lower it to a minimum of 128. Input text is capped at 48,000 characters. These are per-request bounds, not a daily currency budget. Raw API errors are omitted; the helper reports safe exception type/status metadata and records the failed attempt. An incomplete response requires an explicit follow-up rather than an automatic paid continuation.

## Artifacts and dependencies

The helper is [scripts/dev_assistant.py](../scripts/dev_assistant.py). It stores:

- `development/outputs/<run-id>.md`: external development proposal, with an ineligible-for-learner header.
- `development/runs/<run-id>.json`: purpose, model, time, response ID, token usage, status, input/output hashes, and scope. It does not store the input prompt or credential.

Both directories are ignored by Git. Known API-key forms and the loaded credential are redacted from submitted text and output. This is a targeted protection, not a general detector of every possible secret in arbitrary text; provide development material deliberately.

The official SDK `openai==3.31.0` and `python-dotenv==1.2.4` are development dependencies in the existing stable-release lock. The learner runtime does not import them. [Official Python SDK documentation](https://developers.openai.com/api/reference/python), [Responses API reference](https://developers.openai.com/api/reference/python/resources/responses/methods/create).

## Verification

Local checks passed for credential-file loading, development scope, request limits, redaction, usage records, configuration validation, and sanitized failure handling. Ruff checks and dependency/lock checks passed. Temporary validation fixtures used dummy credentials and made no network calls.

One live development-boundary review completed with the configured default model and a 512-token output cap, using **393 total tokens**. The safe [verification receipt](../manifests/development-api-verification.json) records the result and usage. The response's ingestion-boundary recommendation is an external development proposal; enforcing it remains part of future approved implementation work.
