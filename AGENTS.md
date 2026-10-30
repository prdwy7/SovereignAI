# SovereignAI project instructions

Read `docs/DECISIONS.md` and the affected design contracts before changing architecture.
Keep selected designs distinct from implemented and tested capabilities.

## Build approval workflow

The user requires explicit approval before each new build. Follow `docs/BUILD_WORKFLOW.md`.
Present the build ID, roadmap milestone, goal, planned files/changes, dependencies/API use,
verification, and completion criteria. Wait for the user's approval before implementation.
Read-only investigation and preparing/updating the proposal are allowed before approval.
Approval covers routine implementation and checks within that build's scope; seek a new
approval for a material scope expansion. Report results and remaining limits at completion.
Do not start the next build automatically. Track proposals and results in `docs/BUILD_LEDGER.md`.

The user authorized reuse of the existing OpenAI key for **development assistance only**.
Use `scripts/dev_assistant.py` where useful for bounded design/code review, debugging,
test planning, and research planning. See `docs/DEVELOPMENT_ASSISTANCE.md`.

The credential source is referenced by `config/development_api.toml`. Read its key only
through the helper or an equivalent in-memory loader. Never print or copy the key,
include it in command arguments, or inspect secret-bearing files with cat/grep/rg.
No new key or repeated reuse confirmation is needed for this authorized development scope.

Preserve the from-scratch learner: OpenAI output is external development assistance.
It must not become teacher seeds, lexical knowledge, training/practice examples,
learner responses, model embeddings, authoritative graders, or promotion evidence.
Review generated code/fixtures for undeclared English rules, subject knowledge,
and hidden audit answers. Engineering tests may use developer fixtures with explicit scope.
Accepted implementation changes require local checks and ordinary code review.

API requests use explicit text only, fixed token/time limits, no automatic execution,
and metadata-only usage logs. Keep `development/outputs/` and `development/runs/`
out of learner ingestion and source control. Do not start unattended API loops.
