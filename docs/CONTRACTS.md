# SovereignAI initial data and learning contracts

Version 0.3 — 30 October 2026

Most contracts here are design specifications and illustrative authoring examples rather than implemented APIs or accepted teacher seeds. M0.1 has pinned and checked the [Scratch V1/SHA256 format](FOUNDATION_CONTRACT.md); M1.1 implements the [initial Unicode Object collection](../data/objects/unicode/18.0.0/README.md) and a finite declaration registry. Placeholder identifiers in authoring examples below are not actual hashes. Human-facing YAML/JSON is not automatically the hashed identity format.

The core has exactly three persistent primitives: **Object, Relation, Derivation**. Every persistent Object carries a computed identity plus explicit type, definition, schema and payload. Declaration records for types/definitions/schemas are Objects themselves; a pinned bootstrap registry resolves their typed handles to content IDs. Nested reference values, physical files and indexes are implementation structures rather than new primitives. Full general schema/domain validation remains future work beyond the initial registry profile.

M0.2 implements an additional finite [active-object contract](ACTIVE_OBJECTS.md): instance-scoped state, atomic/group membership, observations, explicit transfer policies, operation receipts and replay. Group membership does not transfer experience automatically. These are engineering types over the same three primitives; broader learning contracts below remain proposed.

M0.3 implements the [binary foundation contract](BINARY_FOUNDATION.md): packed observations, scoped immutable pattern concepts, source/evidence references, versioned codebooks, lossless expressions and predictor/evaluation records. Its registry is a new finite profile over the unchanged canonical core. Local prefix codes are not canonical identities or stable neural vocabulary IDs. This baseline supports native bits and a read-only M0.2 adapter while leaving general semantic grounding and the authoring examples below as later work.

The [updated source alignment](BINARY_FOUNDATION.md#source-alignment-and-remaining-concept-learning-work) treats grounded interpretations and learned procedures as separate versioned records with explicit evidence and validation. Existing pattern Objects continue to mean exact scoped patterns. [M1.2](UNICODE_SEQUENCES.md) now implements a finite text registry, strict UTF-8 scalar tokenization, ordered Sequence Objects, byte span maps and verified composition over the same three-primitive core. Its exact original sequence is authoritative; normalized/grapheme and learned lexical views remain future work.

## 1. Domain object families

All families below are typed Objects over the same core primitive.

| Family | Required content | Main invariant |
|---|---|---|
| Symbol | Scalar value, declared repertoire/profile reference | Valid scalar; identity does not depend on rendered glyph |
| Sequence | Ordered child IDs, element profile, exact source representation where relevant | Order and repetitions are committed by content identity |
| Occurrence | Content ID, run/episode, span or event position | Repeated use is distinguishable from repeated storage |
| Concept | Definition/grounding reference, scope, version | A written label alone is not its grounding |
| Lexical entry | Written-form IDs, sense IDs, applicability/context | A form may have several senses |
| Rule version | Input/output schema, pattern/program AST, constraints, scope, predecessor | Executable meaning is defined by the interpreter version |
| Seed assertion | Subject, source, statement/contract, dependency IDs | Teacher authority comes from the input channel, not a self-declared string |
| Lexical source assertion | Source release, record locator, source sense ID, field/relation, attribution, importer version | Import proves a source made an assertion; it does not prove grounding or mastery |
| Lexical exposure | Learner snapshot, activated records, retrieval event and subject scope | Evaluation knows exactly what reference material the learner could access |
| Hypothesis | Claim, assumptions, scope, alternatives, evidence roots | Candidate status cannot self-promote through repetition |
| Task | Goal, context, audience, constraints, visible criterion references | Learner cannot read hidden expected outputs |
| Attempt | Task ID, result, interpretation/derivation references, model snapshot | Assessment binds to this exact immutable version |
| Assessment | Attempt ID, criterion, displayed context, response, assessor, event identity | Yes/No/Think better remain distinct outcomes |
| Evaluation report | Candidate/incumbent, task distribution, metrics, resource use, uncertainty | Reports separate observed performance from targets |
| Promotion | Candidate snapshot, prior snapshot, evaluation references, decision | Rollback can restore the previous active state |
| Checkpoint | Run revision, active state, random/environment state, pending work | Recovery does not duplicate feedback or learning |
| Algebra profile | Operation family, domain/types, basis/shape, numerical conventions, implementation version | An operation needs executable semantics; its name is not an implementation |
| Projection specification | Source snapshot, ordered record references, context/relation filters, weights, codebook/seed, algorithm version | Derived views cannot expose hidden evaluator data or merge scoped meanings silently |
| Derived artifact | Projection ID, blob hash/reference, format/dtype, build receipt, dependencies, approximation measurements | Numerical representations are not authoritative replacements for source records |
| Operator candidate | Typed AST/representation, application order, pre/postconditions, scope, bounds, evidence | Proposals execute only through permitted operations; conditions remain explicit |
| Experiment contract | Baseline/candidate, source exposure, splits, seeds, metrics, budgets, thresholds, permitted changes | Frozen before comparison; the learner cannot rewrite its acceptance conditions |

Relations whose own identity needs to be discussed can be referenced through assertion objects or record-reference objects, because the inspected core's Relation endpoints are Object IDs. Derivations retain typed references to permitted Object/Relation inputs and outputs. Do not silently treat Derivation IDs as Object IDs; introduce an explicit receipt-reference Object when an ordinary semantic Relation must refer to one.

## 2. Foundation bundle authoring template

```yaml
format: sovereign-foundation-authoring-v1
bundle:
  subject: english
  version: 1
  author: teacher
  prerequisites: []
  concept_definitions: []
  lexical_bindings: []
  construction_constraints: []
  assessment_criteria: []
  scope_limits: []
```

The empty lists are intentional. The teacher supplies the actual subject foundations. Approved dictionary records arrive through the separate source-assertion contract in [LEXICAL_RESOURCES.md](LEXICAL_RESOURCES.md). A prepared interface explains the fields without preloading an undisclosed lexicon or grammar.

An illustrative lexical instruction could contain:

```yaml
lexical_binding:
  written_scalars: [0x0063, 0x0061, 0x0074]
  sense_reference: teacher-concept-reference
  grounding_reference: teacher-approved-scene-or-contract
  language_label: english
  evidence_kind: teacher_seed
```

The human language label is metadata. The sequence's lexical meaning comes from the declared concept/grounding and its accepted teaching provenance. The compiler must resolve references and check schemas before accepting the bundle.

The seed compiler has three outcomes: compiled without unresolved ambiguity, compiled candidate awaiting scoped confirmation, or unsupported/unresolved. It must not use a pretrained model to fill missing meanings. A human-facing prose annotation may be retained as uninterpreted text until the learner can understand it.

## 3. Grammar and operation contract

A rule object needs more than a sentence naming a rule. A minimal executable rule representation includes:

```text
rule_version:
  input_schema
  pattern: typed variables and structural constraints
  preconditions: explicit predicates over permitted inputs/context
  program: bounded AST over registered operations
  output_schema
  semantic_effect: role/meaning transformation or predicate
  scope_and_exceptions
  interpreter_version
  supporting_and_opposing_evidence_references
  predecessor_rule_id, if any
```

Program operators initially include `match`, `bind`, `compare_identity`, `compose_ordered`, `select`, `apply_rule`, and `repeat_bounded`. Their exact type signatures and limits are frozen in M0/M3 as appropriate. These are implemented operations over the three primitives, not new persistent primitives.

A proposed sentence construction may map subject, predicate, and object slots to semantic roles. Whether those categories and that ordering are already taught or being hypothesized is recorded explicitly. The interpreter does not assume all English is subject–verb–object, or that one successful construction applies to every clause.

A parse returns a bounded set of interpretations, rule IDs, source spans, and unresolved constraints. Multiple meanings remain visible. A generation result returns a form plus the intended meaning and the derivation connecting them.

## 4. Assessment contract

```yaml
assessment_request:
  request_id: unique-request-id
  attempt_id: exact-immutable-attempt-id
  task_id: task-id
  criterion_id: versioned-criterion-id
  displayed_artifact_id: exact-draft-or-answer-id
  question: Does this version meet the displayed criterion?
  allowed_responses: [yes, no, think_better]
```

The accepted result stores the request, the chosen response, the displayed context, and the assessor event. Repeated delivery of the same result is idempotent. A later genuinely new assessment is a new event. No response leaves the request pending or cancelled, never accepted by timeout.

Example interpretations:

| Question | Yes means | No means | Think better means |
|---|---|---|---|
| Does this phrase identify the indicated referent? | Supports this grounding in this scene | This identification failed | Try a different identification/explanation; label remains unresolved |
| Is this draft clear for the stated audience? | Supports clarity for that task | Clarity criterion failed | Revise and resubmit |
| Is revision B clearer than A? | Supports the stated comparative preference | B did not satisfy this comparison; not necessarily a total ranking | Explore another revision |
| Does this conclusion follow from these premises? | Human support for this inference | Human rejection of this inference | Reconsider the reasoning; do not assume a truth-value label |

A mechanical proof checker can provide a separate result for the last example. Its report does not overwrite the human assessment; disagreement becomes a diagnostic issue.

## 5. Learning update contract

```text
LearningProposal:
  base_snapshot_id
  triggering_task_and_assessment_ids
  affected_rule_or_policy_ids
  proposed_new_records
  explanation_of_candidate_change
  competing_failure_explanations
  diagnostic_task_specification
  required_validation_and_retention_checks
  estimated_resource_and_feedback_cost
```

The explanation is an inspectable proposal, not evidence. Applying the proposal creates a candidate snapshot. Only the promotion manager can make a candidate active after the declared checks. Identical assessment events cannot update counts twice.

If a proposal changes an algebra profile, codebook, rank, tensorization, or derived index, it also names affected artifact/checkpoint versions, rebuild/migration steps, replay tolerances, the experiment contract, and rollback references. These fields are required only for the affected extension. A rank change includes optimizer-state migration; a codebook or graph-view change invalidates dependent retrieval artifacts.

Distinguish an update that follows from an explicit seed instruction, an empirically supported adjustment, and an exploratory hypothesis. Keep rejected candidates available for analysis without letting them enter the active rule set.

## 6. Snapshot and transaction contract

```text
commit_step(
  run_id,
  expected_run_revision,
  step_id,
  verified_immutable_records,
  proposed_active_state_pointer,
  checkpoint_reference
) -> committed_revision | already_committed | conflict | failure
```

`step_id` identifies the logical operation across retries. A conflict requires reloading the current snapshot and reconsidering the proposal. It does not authorize blindly replaying an outdated learning decision.

A run checkpoint includes tokenizer/lexicon/grammar versions, active procedures, curriculum state, calibration state, pending assessment IDs, unfinished environment actions, deterministic random state, and all manifest references. The implementation must capture every state element that affects subsequent decisions.

Deterministic replay requires sorted query results, stable tie-breaking, pinned versions, and fixed numeric behavior where relevant. A log of observations alone is insufficient to replay a stochastic learner. If exact numerical replay is unavailable, record that limitation and define semantic replay tolerances explicitly.

## 7. Retrieval and memory contract

Start with exact IDs, symbol/lexical indexes, typed graph neighborhoods, dependency indexes, and contextual filters. No pretrained semantic vector index is required. Learned association scores may be introduced from the system's own experience.

Every retrieval request specifies a snapshot, purpose, context, node/edge budget, depth limit, and deterministic tie-breaking. The answer includes selected records and truncation/coverage information. The learner must not equate a bounded search returning nothing with proof that no relevant knowledge exists.

Separate hot working memory, persistent experience, active rules, and archival candidates. Consolidation may change indexes and active views. It cannot erase the supporting evidence of an active claim without either preserving a reconstructible archive reference or explicitly withdrawing the claim.

Retention/compaction policies must preserve seeds, accepted rule dependencies, unresolved contradictions, assessment records, and audit results. Measure graph growth before choosing pruning thresholds. Evidence required for reproducibility is retained or exported with content hashes.

## 8. Initial failure and acceptance checks

The first complete integration exercise must show all of the following:

1. The same scalar/sequence content under the same format produces the same ID across restart.
2. Repeated symbols preserve positions; changed order changes sequence identity.
3. The graph reconstructs the sequence and identifies the exact composition rule.
4. Hash-valid but domain-invalid output is rejected by the appropriate domain check.
5. A seed establishes a lexical binding without requiring the learner to parse its own teaching interface.
6. Yes, No, and Think better are stored and acted on differently.
7. A delayed response updates only its original attempt and applicable candidate state.
8. A retried database transaction does not duplicate an assessment or learning update.
9. A crash during an unfinished assessment/action resumes without inventing an outcome.
10. A rejected or rolled-back rule leaves the historical evidence intact.

This contract set is expanded as milestones introduce grammar, reasoning, drafting, mathematics, and a second storage backend.

## 9. Mathematical extension and derived-artifact contract

The AX01–AX12 designs in [MATHEMATICAL_EXTENSIONS.md](MATHEMATICAL_EXTENSIONS.md) use the existing primitives and promotion protocol. Each numeric view must declare its source snapshot, ordered inputs, context/sense filters, algebra profile, code/algorithm version, seed and PRNG, dtype/backend/device, dimensions/ranks, budget, and artifact content hashes. Large matrices and indexes are external blobs referenced by typed Objects.

An artifact has explicit candidate/evaluated/accepted/rejected/stale/retired state. A query specifies the required snapshot and coverage policy; a mismatch produces a stale/unsupported result, an explicit rebuild, or an exact fallback. Empty approximate retrieval never establishes that a fact is absent. Returned candidates retain canonical IDs and are checked against exact records before use.

Ordered application must be unambiguous. An operator program applying `append_a` followed by `append_b` to an empty sequence yields `ab`; reversing application yields `ba`. Hashes, source spans, and role bindings must preserve this distinction. A commutative vector-binding operation requires explicit role/position encoding when used to approximate these records.

Cost, similarity, projection error, and compatibility residual are different score types. They require units or interpretation, scope, and provenance; none automatically becomes truth probability. Exact record identity is verified byte-for-byte, while numerical replay uses declared tolerances when exact replay is unavailable.

Each extension's experiment contract includes:

```text
extension_ids, implementation_manifest, permitted_parameter_changes
baseline_snapshot, candidate_snapshot, graph_and_artifact_versions
source_exposure_manifest, train_validation_audit_partitions
reference_checker, task_generator_version, seeds_and_random_state
metrics_with_units, resource_and_feedback_budgets, acceptance_limits
hard_invariants, retention_tasks, rollback_snapshot
```

The [draft TOML register](../experiments/mathematical_extensions.toml) is a design checklist, not an implemented API or runtime activation mechanism. An implementation must validate and complete the experiment contract before execution.

Additional acceptance cases cover role-swapped HDC cues, stale graph projections, sparse-index supersession, min-plus ties/unreachable paths, operator-precondition violations, tensor/rank checkpoint migration, legitimate cross-context disagreement, and rare errors hidden by multiscale summaries. None changes Yes/No/Think better semantics or permits evaluator access.

## 10. Accepted numeric/tensor scaling direction — future implementation

The user adopted this as the fundamental scaling design for later M0.3 improvements on 30 October 2026. The normative design is recorded in [BINARY_FOUNDATION.md](BINARY_FOUNDATION.md#accepted-scaling-design-numeric-values-tensors-and-bulk-storage); the following schemas and operations are not yet implemented.

- Counts, dimensions, indices, lengths and offsets use exact integers, initially checked uint64. Derived shape products and byte ranges reject overflow. Floating-point value format and parameter count are separate fields/contracts.
- A logical tensor Object declares dtype, shape, layout, canonical byte order, exact byte length and canonical uncompressed-content digest. A storage-representation Object separately binds that tensor to codec/codebook versions and ordered chunk manifests.
- Chunk descriptor Objects record logical offsets/lengths, stored lengths, stored/decoded hashes and adapter-managed locators. Dense manifests verify complete non-overlapping coverage; other layouts require explicit schemas. Large manifests use bounded pages.
- Graph records hold descriptors and provenance; external binary artifacts hold packed values. An individual parameter may be referenced by tensor ID and a checked index without materializing one full graph Object per weight.
- Lossless recompression/rechunking preserves the logical tensor descriptor and canonical content. Updates or lossy transforms create new logical versions. Derivations record source/result versions and executable conversion contracts; evaluation records declare error and retention evidence for approximate transforms.
- Streaming and checkpoint operations have explicit memory/I/O budgets, integrity checks and staged-versus-committed recovery semantics. Canonical identity remains exact even when numerical execution replay uses a declared tolerance.

All descriptors remain ordinary typed Objects; links remain Relations; computation/change history remains Derivations. Adopting these contracts does not change the current M0.3 bit-length/collection limits, grant the learner arithmetic knowledge, or demonstrate large-model storage/execution.
