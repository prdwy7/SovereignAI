# User-approved builds

Effective **30 October 2026**, at the user's request: explain what is being built in relation to the roadmap and goals, and obtain approval for each build before implementation.

## Build proposal

Before a new build, present:

1. **Build ID and milestone:** a bounded slice such as M0.1, linked to the main roadmap.
2. **Goal:** the observable result and why it advances SovereignAI.
3. **Current state:** existing dependencies, relevant evidence and unresolved choices.
4. **Scope:** deliverables, expected files/areas, and material limitations.
5. **Dependencies and API use:** package/service changes and any bounded OpenAI development assistance.
6. **Verification:** meaningful checks and the evidence required for completion.
7. **Approval request:** wait for the user's explicit approval before implementing the slice.

Preparing the proposal, read-only investigation, and recording the user's instructions are allowed before approval. Approval authorizes routine edits, fixes, checks and the declared API assistance within that build. A material scope expansion needs another approval; routine repairs within scope do not require approval per file or command.

## During and after the build

Provide progress tied to the approved goal. Record blockers or changed assumptions clearly. At completion, report what changed, what passed, what remains uncertain, and where the result can be reviewed. Update the [ledger](BUILD_LEDGER.md), then propose the next slice separately. Do not mark an entire roadmap milestone complete because one slice passed.

The user can narrow, cancel or redirect a build at any point. A proposal or a lack of response is not approval. Approval of one build does not automatically authorize the next.

## Latest completed build: M1.2

The user approved [M1.2](M1_2_PROPOSAL.md) and requested API-authored implementation with Codex inspection. It is complete: reversible scalar tokenization, ordered Sequence Objects, spans, replay, bounded persistence and recovery. [170 tests and four reproducible artifacts](UNICODE_SEQUENCES.md) provide the local evidence. The expanded API authoring scope was explicit in the approval; nine bounded requests are recorded. Remaining graph, concept-learning and scaling builds need separate approval.

## Initial next build proposal: M0.1

**Goal:** choose and pin the Silicate foundation contract before building the Unicode importer or graph learner.

**Scope:** inspect the two local Silicate variants already identified in the plan, compare their Object/Relation/Derivation formats, review the relevant code/license boundaries, recommend and pin one format/revision, and produce compatibility fixtures and a minimal validation procedure. If license or compatibility evidence prevents selection, return that finding with a concrete alternative rather than copying incompatible formats together.

**Expected deliverables:** a foundation comparison/decision note, a source/format manifest, canonical-record fixtures for all three primitives, and round-trip/strict-validation evidence. Expected areas are `docs/`, `manifests/`, `fixtures/`, and only the minimal integration/check code needed for this contract.

**Dependencies/API:** use existing local sources and tools first. One bounded OpenAI development review may inspect the contract proposal or non-secret code excerpts; local checks establish correctness. Report a needed package/build dependency before materially expanding the scope.

**Completion evidence:** the selected format is reproducibly identified; valid fixtures round-trip with stable identity; malformed or mismatched records fail; order-sensitive composition is explicitly specified. This is a foundation-contract slice, not completion of M0 or a demonstration of English learning.

**Status:** M0.1 explicitly approved and completed; see [FOUNDATION_CONTRACT.md](FOUNDATION_CONTRACT.md). M1.1 was subsequently approved and completed: first-level Unicode Objects, engineering declarations, canonical collection, lookup index and verification. See the [collection guide](../data/objects/unicode/18.0.0/README.md). Approval of these slices does not complete all of M0 or M1, or authorize the next expansion build.

## Approved M0.2: object interaction and state transitions

**Status: completed — 30 October 2026.** The user approved M0.2 and clarified that interaction scope belongs to the atomic or composite instance, with connections but no implicit transfer of group experience into member state. The implementation includes flat groups of active atoms and an explicitly invoked group-to-member observation transfer rule. Group creation starts a fresh history; existing members retain their independent histories. Subjective experience and its potential usefulness remain open research hypotheses, not acceptance criteria or implemented capabilities. See [the implemented contract](ACTIVE_OBJECTS.md) and [verification receipt](../manifests/m0-2-verification.json): 67 tests pass, the complete demo replays identically, and hard exits before/after commit recover correctly. The scope below preserves the approved proposal; no next build is authorized automatically.

Conscious experience remains a separate research question. Current research proposes theory-derived indicators while emphasizing uncertainty about consciousness and its assessment; adding memory, a self-reference or a response loop is not a validated consciousness test. See [Butlin et al., Identifying indicators of consciousness in AI systems](https://doi.org/10.1016/j.tics.2025.10.011).

**Roadmap and goal:** a bounded part of M0's operation contracts, using completed M1.1 Unicode Objects and preparing for M2's resumable interaction harness. Demonstrate an observation changing an active instance's state, with a reproducible Derivation and recovery after restart. This does not complete M0, M1 or M2.

**State before this build:** the canonical three-family codec, finite Unicode declaration registry and scalar collection were implemented. The operation executor, general domain registry, active-state store and learning harness were not. M0.2 now supplies a bounded executor, finite registry extension and active-state store; the general domain interpreter and learning harness remain future work. Unicode records do not execute behavior themselves.

### Proposed representation and execution

| Part | Representation and responsibility |
|---|---|
| Referenced symbol | Existing immutable Unicode Object |
| Active instance | Typed Object binding a particular run/instance to its symbol and execution configuration |
| Observation | Typed Object with source, instance, unique event identity and observed Object reference |
| State version | Typed Object committing to its instance, prior state, processed observation and bounded memory/counters |
| Rule and result | Typed Objects with explicit executable contract/version and structured result |
| Connections | Relations between Object IDs, such as state-of, observes and supersedes |
| Transition receipt | Derivation naming ordered inputs, rule/version, parameters and resulting Objects/Relations |
| Runtime | Shared Python executor for explicitly registered operations; stored records do not execute themselves |

All new Object types require declaration Objects and an explicitly versioned registry extension. The existing Unicode profile and collection remain valid. A changing state creates a new Object ID; a stable active-instance Object links its history. There is no fourth persistent primitive. Relation endpoints remain Object IDs; any graph link to a Derivation uses an explicit receipt-reference Object as required by the existing contract.

Instantiate only the selected working set on demand. No per-character process or continuously running loop for the entire Unicode collection is needed. The initial operations are identity comparison and bounded state update. Their behavior is engineered and must not be reported as learned language or learned reasoning.

**Demonstration:** bind an instance to U+0041 and present three distinct events containing U+0041, U+0042 and U+0041. The runtime records match, mismatch, match, with three observations and two matches. Replaying the same event identity must not count it twice; a new event containing the same scalar must count as a new observation. These are developer engineering fixtures, not language lessons. Symbol meaning remains unresolved.

### Scope, dependencies and evidence

**Planned files:** `tools/active_objects.py` for the bounded executor, local persistence and inspection CLI; `tests/test_active_objects.py`; `fixtures/active-objects-v1/`; a contract note under `docs/`; a verification receipt under `manifests/`; isolated demonstration output under `data/experiments/active-objects/m0-2/`; and updates to the build ledger and architecture status. Existing codec changes are limited to reusable validation needed by this declared prototype. Keep prototype output excluded from learner ingestion.

**Storage:** a separate local store for canonical Object/Relation/Derivation records and a rebuildable SQLite index. Publish each complete step through an atomic SQLite transaction containing its records and active-state pointer. The immutable Unicode pack remains the source of scalar references. This is prototype persistence; the planned Neo4j adapter remains a separate build.

**Dependencies/API:** existing Python 3.11 environment and standard-library SQLite, with the installed test tools. No additional package, neural model, database service or pretrained learner. At most one bounded OpenAI development review through the existing helper, with a 1,024 output-token cap; its output cannot become learner knowledge or acceptance evidence.

**Completion criteria:** all new records round-trip and resolve declarations; source Unicode identities stay fixed; deterministic replay reproduces state and receipt IDs; stored receipts are checked by re-executing the registered operation; duplicate events are idempotent; distinct repeated observations remain distinct; invalid references and unsupported rules fail; restart resumes only committed steps; interruption cannot expose half a transition; and configured step/memory limits stop execution. Run the existing regression suite plus the new execution/recovery checks. Report observable behavior and limits without a sentience or language-understanding claim.

**Later, separately approved research:** sequence and concept interactions, learned predictions, scoped uncertainty, diagnostic experiment selection, a representation of system capabilities and limits, and independently evaluated rule revision. These need grounding, feedback and validation; activity alone supplies none of those guarantees.

## Authorized M0.3: binary internal-language foundation

**Status: completed, 30 October 2026.** The user directly requested implementation of [the shared binary-language design](https://chatgpt.com/s/t_6ae44d42ba6481918fec6b463eb8ccf5) as foundational. That request authorized this concrete implementation; it does not authorize unrelated subsequent builds. The public page exposes one assistant response, including six architecture components embedded in its visual markup. Earlier private messages are not available. The [implemented contract](BINARY_FOUNDATION.md) and [verification receipt](../manifests/m0-3-verification.json) record 103 passing tests, reproducible native/adapter artifacts, exact reconstruction, source-scope preservation and both successful and unfavorable cost measurements. The scope below preserves the authorized build description.

**Goal and roadmap:** implement a bounded executable baseline for all six components: binary observation, pattern discovery, candidate concept formation, statistical relationship discovery, binary representation optimization, and prediction/reconstruction validation. This extends M0/M1 representation and prepares later concept learning/M4; it does not complete language mastery or general reasoning.

**Architecture decisions:** retain exactly Object/Relation/Derivation and their immutable identities. Unicode becomes a supported observation adapter, not a requirement that all internal concepts have English labels. Candidate concepts are scoped bit patterns with explicit observational support. Short local prefix codes are versioned mappings to immutable concept IDs. Group/member scope boundaries and root provenance from M0.2 remain intact. No arbitrary rewriting of executable instructions or implicit transfer between instances.

**Files and implementation:** binary packing/prefix-code functions, a deterministic discovery/encoding/evaluation pipeline and CLI under `tools/`; engineering-only fixtures and tests; immutable canonical record collections and reports under `data/experiments/binary-language/m0-3/`; source and verification receipts under `manifests/`; updated foundation/architecture/decision documents. Existing M0.2 artifacts remain independently verifiable. Add a read-only adapter for one selected active instance's committed observation history.

**Algorithms and evaluation:** bounded repeated-substring discovery with evidence-root deduplication, candidate pattern Objects, observed-following Relations, deterministic Huffman coding as an initial entropy-coding baseline, raw-bit fallback, and a learned frequency-based next-bit predictor compared with a majority baseline. Fit/selection use training observations only. Holdout roots are disjoint. Exact reconstruction is a hard constraint; account for dictionary, framing, packing and ID overhead. Report encoding work, decoding work and prediction error separately, with explicit integer objective weights. Compression improvements are not evidence of semantic understanding.

**Dependencies/API:** Python 3.11 standard library and existing test tooling, no new package/model/database service. At most one bounded OpenAI development review (1,024 output-token cap) if useful; it cannot supply learner observations, labels or acceptance evidence. The referenced chat supplies architecture guidance, not training data; its illustrative English concepts and example binary labels are not imported.

**Completion evidence:** exact reconstruction including non-byte-aligned inputs; malformed-code/padding rejection; immutable concept identity across codebook changes; only three persistent families with resolved declarations; full deterministic record replay; no train/holdout leakage or cross-scope evidence pooling; raw fallback on unsuitable data; reproducible fixture and M0.2-adapter demonstrations; existing regression/dependency checks. More advanced MDL models, information bottleneck, vector quantization, hierarchical RL, general program synthesis, learned graph models, emergent communication and arithmetic coding remain research options rather than dependencies claimed implemented.
