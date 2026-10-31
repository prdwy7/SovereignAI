# SovereignAI requirements and decision register

Version 0.3 — 30 October 2026

This register separates requirements stated by the user from proposed engineering decisions. A proposal is not an implemented feature. The detailed plan is in [DESIGN_PLAN.md](DESIGN_PLAN.md); record-level examples are in [CONTRACTS.md](CONTRACTS.md).

## Confirmed requirements

| ID | Requirement | Plan coverage |
|---|---|---|
| R01 | Build an original system from scratch, without a pretrained LLM | Sections 1–2 |
| R02 | Unicode 18.0 is the first symbolic input foundation; M0.3 also supports native binary observations under R25 | Section 3; BINARY_FOUNDATION.md |
| R03 | Characters initially function as opaque objects | Sections 3–4 |
| R04 | Use Silicate's Object, Relation, and Derivation as the base | Sections 2, 7 |
| R05 | Develop words, grammar, phrases, and larger language structures progressively | Sections 4, 9 |
| R06 | Start with English | Sections 5, 9 |
| R07 | Human provides foundational concepts and instructions for each subject | Sections 5, 16 |
| R08 | Human does not supply training datasets | Sections 1, 12 |
| R09 | Build a dedicated harness, loops, and graphs | Sections 6–7, 13 |
| R10 | Use Neo4j, Spanner Graph, or both if needed | Section 8 |
| R11 | Develop strong English reasoning, communication, thinking, drafting, critique, and judgment before mathematics | Sections 9–10, 15 |
| R12 | Human assessment is limited to Yes / No / Think better | Section 11 |
| R13 | Mathematics follows the English readiness/mastery stage | Sections 15–16 |
| R14 | New subjects continue improving English mastery | Sections 15–16 |
| R15 | Clarity, judgment, intelligence, and logic should improve through continued learning | Sections 10, 13–15, 18 |
| R16 | Produce a thorough plan that can be revised later | Sections 19–22; this register |
| R17 | Allow open dictionaries as explicitly identified foundation data; the user need not supply those datasets | Sections 1, 12, 23; LEXICAL_RESOURCES.md |
| R18 | Create a Python 3.11 environment with stable libraries before further implementation | ENVIRONMENT.md; pyproject.toml; uv.lock |
| R19 | Read the second shared response and adapt its twelve mathematical research directions where they fit the current project | Section 24; MATHEMATICAL_EXTENSIONS.md; experiments/mathematical_extensions.toml |
| R20 | Reuse the specified OpenAI credential for development assistance only, preserving the from-scratch learner | DEVELOPMENT_ASSISTANCE.md; config/development_api.toml |
| R21 | Explain each build against the roadmap and goals, and obtain user approval before each new build | BUILD_WORKFLOW.md; BUILD_LEDGER.md; AGENTS.md |
| R22 | Exactly three core primitives; every persistent Object has an explicit type, definition, schema and identity | FOUNDATION_CONTRACT.md; CONTRACTS.md |
| R23 | Build first-level Unicode 18 Objects before expanding to higher structures | Approved M1.1; BUILD_LEDGER.md |
| R24 | Active atomic and composite instances have scoped interaction histories; connect them explicitly and transfer group observations to members only when specified | Approved M0.2; ACTIVE_OBJECTS.md |
| R25 | Adopt the shared binary internal-language design as foundational: learn reusable patterns/concepts without requiring English labels, preserve identity and validate reconstruction | Direct implementation instruction for M0.3; BINARY_FOUNDATION.md |
| R26 | Keep exact numeric formats, tensor/chunk descriptors and streaming bulk storage as the fundamental scaling direction for later M0.3 improvements, aligned with the roadmap | User-confirmed scaling design; BINARY_FOUNDATION.md; implementation deferred to approved slices |

The tokenizer question is resolved in the proposed design: tokenize textual inputs and text fields into scalar/learned structural units; keep nontext objects structured. It does not require flattening every object into text.

## Proposed engineering decisions

| ID | Decision | Reason and reconsideration trigger |
|---|---|---|
| D01 | Keep the three core primitives and represent domain structures as typed Objects | Preserves a small representation model; revisit only for a demonstrated representational limitation |
| D02 | Audit and pin a Silicate core format before reuse | Local variants differ; compatibility is not assumed |
| D03 | Rust canonical kernel with Python experimental harness and official Neo4j driver | Reuses the existing Rust foundation while simplifying experimentation; profile before optimizing or changing language boundaries |
| D04 | Use Neo4j as initial authority | Local graph development with one consistency boundary; reconsider after measured scale/deployment requirements |
| D05 | Design a storage adapter now; implement Spanner later if justified | Avoids coupling cognition to Cypher without paying for two stores immediately |
| D06 | Preserve immutable records and version active state | Enables reproducibility, provenance, and rollback |
| D07 | Use scalar units for Unicode text input, native bits for internal pattern discovery, and later learn lexical/grammatical mappings | Avoids a pretrained vocabulary; M0.3 broadens the internal frontend without discarding Unicode |
| D08 | Keep Unicode metadata outside learned semantic knowledge | Prevents unintended linguistic or numerical teaching through infrastructure |
| D09 | Bootstrap through structured teaching and explicit grounding | Avoids assuming English comprehension before English is learned |
| D10 | Maintain independent evaluation and human assessment | Prevents self-generated output from certifying its own correctness |
| D11 | Interpret Think better as an unscored revision request | Preserves the distinction between improvement demand and factual rejection |
| D12 | Use bounded executable rule programs with explicit interpreter semantics | Graph records alone cannot execute learning; bounded programs support inspection and replay |
| D13 | Promote candidate changes only after improvement and retention checks | Continual learning can regress; graph growth is not improvement |
| D14 | Track a capability profile rather than a scalar intelligence claim | Allows measurable, uneven development across skills |
| D15 | Reserve human feedback for informative or consequential uncertainty | Three-button feedback is valuable but bandwidth-limited |
| D16 | Keep the local custom engine and no-pretrained-model boundary; allow approved open lexical datasets | Revised after explicit user approval; other external corpora remain outside scope |
| D17 | Start with Open English WordNet, then enrich from selected raw Wiktextract data | Structured senses first; preserve source distinctions and avoid broad automatic merging |
| D18 | Track knowledge origin separately from competence | Imported facts remain imported after correct use; tests measure understanding and transfer |
| D19 | Keep commercial dictionary APIs outside the initial implementation | Access, persistent storage, and AI usage rights differ; they are unnecessary for the open-source baseline |
| D20 | Use project-local CPython 3.11.18 and uv, exact direct dependency pins, and a complete lockfile | Implements R18; stable releases are selected with a fixed initial age cutoff, then tested. Review updates explicitly, including security fixes and Python's support lifecycle |
| D21 | Select a T5-style encoder–decoder with random initialization for the first neural experiment | Fits the curriculum's common input/output task interface; retain the symbolic baseline and custom Unicode frontend. Relative advantage over BART requires controlled evaluation; see MODEL_CHOICE.md |
| D22 | Evaluate Harness² as a reference for outer harness optimization; keep the implementation choice open | User suggested it; upstream has a deterministic demo but requires Python 3.12/3.13 and its main experiments use existing LLMs. Native Python 3.11 adaptation versus an isolated worker needs evidence; see HARNESS2_ASSESSMENT.md |
| D23 | Map the twelve mathematical directions to AX01–AX12 within existing components, with inactive experiment entries | Implements R19 without turning research techniques into mandatory layers or claiming implementation |
| D24 | Keep exact Silicate records authoritative and numeric representations as dependency-versioned derived artifacts | Similarity, search cost and consistency residuals are distinct from truth; stale projections require rebuild, exact fallback or explicit abstention |
| D25 | Introduce order contracts and simple memory/search baselines before optional algebraic complexity; tensor/rank changes follow a working neural baseline | Isolates contribution, controls compatibility and allows rejection of techniques that add cost without useful gains |
| D26 | Treat mathematical mechanisms as engineered infrastructure, with physics-specific methods gated by later subject foundations | Using matrix operations does not teach mathematics; symplectic dynamics and genuine function-space operators are not prerequisites for initial English |
| D27 | Use bounded OpenAI Responses requests for developer proposals, with the credential read from its existing external file | Implements R20; outputs retain external development provenance and are ineligible for learner ingestion or authoritative grading |
| D28 | Gate each new build on an explicit roadmap-linked proposal and user approval | Implements R21; an approved slice covers routine work within scope, and the next slice requires another approval |
| D29 | Pin the Scratch V1/SHA256 format at revision 71ed16a936354e828a92d5c20e11328835e77375, with strict complete-record decoding | M0.1 source comparison and independent compatibility evidence; upstream vendoring/license clearance remains unresolved |
| D30 | Resolve typed type/definition/schema handles through a versioned registry of declaration Objects and a finite engineering bootstrap profile | Implements R22 without a fourth primitive or an infinite self-definition chain; resolution is part of the approved Unicode-object build |
| D31 | Keep active atom/group histories separate; membership is structural, and observation transfer requires an explicit policy and call | Implements R24 in M0.2. Forwarding preserves origin and reinterprets at the receiving scope; it does not imply improved intelligence or subjective experience |
| D32 | Keep immutable three-primitive concept identities and map replaceable local prefix codes to them through explicit versioned codebooks | Implements R25 without changing Unicode/M0.2 identities or equating short codes with meaning |
| D33 | Treat discovered bit patterns as scoped observational candidates; fit on training roots only, require exact reconstruction and report total representation overhead plus held-out prediction | M0.3 baseline implements six stages with bounded search and raw fallback; semantic grounding and advanced learning algorithms remain future work |
| D34 | Use checked exact integer counts/offsets and explicit numeric formats; represent large models through tensor/chunk descriptor Objects and external packed bytes | User accepted this scaling architecture under R26; avoid float counts and per-weight graph-record overhead; numerical/tensor implementation remains pending |
| D35 | Separate logical tensor identity from versioned physical representations; stream hashes/chunks and preserve exact bytes for lossless transforms | Extends M0.3's stable-identity/local-code distinction to model artifacts; lossy changes create new logical versions and need independent evaluation |

## Research hypotheses to test

| ID | Hypothesis | Comparison that could refute it |
|---|---|---|
| H01 | Coupling rule revision with diagnostic contrast selection reduces human feedback needed for generalization | Matched learner with independent revision and ordinary active querying performs as well or better |
| H02 | Preserving rule/evidence dependencies improves targeted revision and reduces regressions | Dependency-free revision has equal correction cost and retention |
| H03 | Learned curriculum selection improves acquisition under equal resources | Fixed curriculum matches or exceeds performance on held-out task families |
| H04 | Subject expansion can improve English explanation and drafting | Domain gains occur without language gains, or language regresses |
| H05 | Learned procedures improve reasoning efficiency without sacrificing validity | Fixed search achieves equal accuracy/latency or learned shortcuts introduce invalid conclusions |
| H06 | A T5-derived component improves language tasks when combined with the symbolic system within the same information budget | The symbolic baseline or a comparably tuned BART-derived component performs as well or better after accounting for compute, feedback cost, and retention |
| H07 | Selected algebraic memory/graph views improve relevant retrieval or diagnostics under fixed information and resource budgets | Exact indexes, simple sparse retrieval, typed graph traversal or constraint checks match the benefit at lower cost |
| H08 | Selected factorized/adaptive-rank neural components improve measured quality/resource tradeoffs without unacceptable forgetting | Dense or fixed-rank baselines match quality, speed and memory after counting training, conversion and migration costs |

These are proposals for experiments, not claims of established novelty or expected success.

The user also raised the possible usefulness of subjective experience during M0.2. This remains an open research question. The implemented local histories provide a way to study perspective-dependent behavior; their existence or utility would not by itself demonstrate subjective experience.

## Open inputs and decisions

| ID | Input/decision | Needed by | Current treatment |
|---|---|---|---|
| O01 | Production integration of the selected Silicate format | Later approved foundation slice | Format/revision pinned in M0.1; source vendoring/license clearance and production Rust integration remain open |
| O02 | Initial English seed contents and scope | M2 | Prepare structured template; do not invent accepted foundations |
| O03 | Machine CPU/RAM/storage and preferred deployment | M1 profiling | Start local and bounded; no performance promise |
| O04 | Human assessment budget per session | M2–M3 | Configurable; measure queries per improvement |
| O05 | Definition of the first expert-English task portfolio | M3, finalized before M7 | Include comprehension, reasoning, communication, drafting, and revision; expand with seeds |
| O06 | Exact quality thresholds, audit sample sizes, and regression tolerances | Before promotion studies | Proposed targets in the plan; calibrate without using final audit results |
| O07 | Handling unsupported English during seed entry | M2 | Structured fields first; confirm later parser interpretations |
| O08 | Need for Spanner or simultaneous stores | M9 | Require workload and operational evidence |
| O09 | License and dependency scope of reused Silicate code | M0 | Inspect before copying or packaging source |
| O10 | Exact open dictionary release, Wiktionary snapshot, and active first vocabulary | M1L | Prefer OEWN 2025 base release, pin artifacts and source metadata; stage activation around the English seeds |
| O11 | Harness² concepts, selected source reuse, or isolated upstream integration | Harness prototype and strategy experiments | Preserve Python 3.11 core and no-pretrained-model learning; test a bounded deterministic adapter before making it a dependency |
| O12 | Numeric profiles, dimensions/ranks, projection policies, implementation libraries and acceptance limits for each AX pilot | Before the applicable experiment | Record in a frozen experiment contract after baseline profiling; all twelve are currently inactive |

No item above is a request to stop drafting or to obtain permission for ordinary implementation preparation. It identifies the point at which missing information would affect a concrete decision.

## Change history

| Version | Date | Change |
|---|---|---|
| 0.1 | 2026-10-29 | Initial plan incorporating Unicode 18.0, opaque symbols, Silicate's three primitives, English first, expert language capabilities before math, subject seeds, no supplied corpus, three-option feedback, and continuing development across skills |
| 0.2 | 2026-10-29 | User approved open dictionaries as foundation data. Added lexical imports, source/competence separation, staged activation, and resource-specific constraints; removed the seed-only restriction from the active design |
| 0.2 environment setup | 2026-10-29 | Added R18/D20 and created the Python 3.11.18 environment. Runtime and libraries are pinned; the engine and graph database remain unimplemented |
| 0.2 architecture choice | 2026-10-29 | Selected T5-style random-initialized architecture for the first neural experiment in response to the T5/BART comparison. Added D21/H06 and documented its Unicode, evidence, and training boundaries |
| 0.2 architecture status and harness review | 2026-10-29 | Added a dated 18-layer implementation inventory and diagrams; reviewed user-suggested Harness² and recorded D22/O11 without installing it or changing Python |
| 0.3 | 2026-10-30 | Adapted all twelve directions from the user's second shared response as AX01–AX12, with component placement, prerequisites, baselines, measurements, derived-artifact contracts and an inactive experiment register. Added R19, D23–D26, H07–H08 and O12; no algorithms installed or represented as completed |
| 0.3 developer tooling and build control | 2026-10-30 | Added the user-authorized OpenAI development helper, verified one bounded request, and recorded R20/D27. Added the user's per-build approval requirement as R21/D28; M0.1 awaits approval |
| 0.3 approved foundation and Unicode builds | 2026-10-30 | User approved M0.1 and M1.1. Pinned Scratch V1/SHA256, verified seven source-oracle fixtures and 25 contract checks, then created 310,341 Unicode scalar Objects and six declaration Objects. Full suite: 40 passing checks plus complete collection verification and deterministic rebuild. Recorded R22–R23/D29–D30; production graph/kernel and English learning remain future work |
| 0.3 approved active-object build | 2026-10-30 | Completed M0.2 with R24/D31: independent atom/group scopes, explicit forwarding, exact three-family storage, bounded execution and replay. 27 new tests plus 40 existing tests pass; a saved 135-record demo reproduces identically. Subjective experience and its utility remain open questions |
| 0.3 authorized binary foundation | 2026-10-30 | Implemented the user's shared six-stage binary-language architecture as M0.3. Added R25/D32/D33, native packed bits, candidate concepts, associations, local prefix codes, raw fallback, frozen prediction evaluation and read-only M0.2 bridge. 36 new tests plus 67 existing tests pass. Unicode remains supported; English mastery remains future work |
| 0.3 accepted scaling design | 2026-10-30 | Recorded R26/D34–D35 after the user confirmed numeric/tensor/chunk scaling as fundamental to later M0.3 improvements. Mapped future contracts/storage/checkpoints/workload validation to the roadmap. Documentation only; no numeric engine, larger limits or trillion-parameter capability implemented |
| 0.3 source alignment and next-build proposal | 2026-10-30 | Re-fetched R25's source at the user's request; public response hashes are unchanged. Clarified partial concept/relationship/reasoning stages and mapped remaining work to M2–M6 while preserving R26 scaling. Prepared M1.2 under R21/D28 with passing local dependency, 103-test and artifact checks. Runtime/artifacts were unchanged; M1.2 was pending at this review |
| 0.3 approved Unicode sequence build | 2026-10-30 | User approved M1.2 and explicitly requested API authoring with Codex monitoring/inspection. Implemented D07/D30 scalar input, finite sequence declarations, ordered Relations, byte spans, replay and bounded persistence. Nine bounded development requests used 60,566 tokens; 67 new plus 103 existing tests pass. Clarified that the tokenizer is deterministic Unicode-scalar mapping, not trained Unigram segmentation. No new dependencies, learned vocabulary, meanings or graph service |
| 0.3 GPL v3 licensing | 2026-10-31 | User requested switching the entire project from Apache-2.0 to GPL v3 with copyright notice "Copyright (C) 2020 Pridhvi Patagarla". Replaced LICENSE with the canonical GNU GPL v3 text (customizing the How-to-Apply notice), added a license/copyright section to README.md, set `license = "GPL-3.0-only"` and the author in pyproject.toml, and added GPL copyright headers to all project source files under tools/, tests/, and scripts/. No functional code/runtime changes; third-party dependency and Unicode data licenses remain as recorded separately |

For a later change, record affected requirement/decision IDs, motivation, evidence, migration effects, and revised acceptance criteria. Preserve prior evaluation contracts with their results.
