# M0.1 Silicate foundation contract

Completed 30 October 2026 under explicit user approval. Format identifier:
`sovereign-silicate-scratch-v1-sha256`.

## Exactly three primitives

The persistent core families are **Object, Relation, Derivation**. Every later entity uses these primitives. Words, concepts, definitions, schemas, models, checkpoints and artifact descriptors are typed Objects; links are Relations; computation history is recorded as Derivations.

The reference codec's `Reference` is a nested field value inside a Derivation, not a fourth record family. It cannot be encoded or decoded as a standalone primitive. Other implementation helpers, registries, indexes and physical containers do not add semantic primitives.

Every Object has a computed content identity and explicit type, definition, schema and payload. Definition/schema declarations are represented as Objects and resolved through a versioned registry. Typed definition/schema handles are not silently treated as Object IDs: the registry explicitly maps each handle to its declaration Object. A finite engineering bootstrap profile supplies the initial declaration handles and validation rules, avoiding an infinite chain of definitions defining themselves. These engineering contracts do not confer English meanings on the learner.

M0.1 pins encoding, identity and strict decoding. Definition-reference resolution and durable storage belong to the approved M1.1 Unicode-object slice. Synthetic M0 fixtures intentionally use opaque test handles and are not accepted learner objects.

## Source decision and boundaries

Selected reference: local `SilicateScratch`, revision
`71ed16a936354e828a92d5c20e11328835e77375`, with per-file SHA-256 pins in
[silicate-foundation.json](../manifests/silicate-foundation.json).

| Concern | SilicateScratch | RustSilicate |
|---|---|---|
| Object types/schema | Extensible 32-byte type, definition and schema handles | Closed type enum, definition handle and integer schema version |
| Relation | Ordered edge plus context bytes | Ordered edge, no context field |
| Derivation | Execution class; Object/Relation references | Object references only |
| Identity construction | Domain tag followed by canonical bytes, whose first byte is protocol 1 | Separate protocol byte added by hashing; record layouts differ |
| Reproducible source pin | Git revision and file hashes | Inspected-file hashes; directory has no Git repository |

The Scratch format fits the planned extensible object model and provenance. These formats are not wire-compatible. No automatic reinterpretation/migration is implemented.

No explicit license was found in the inspected top-level license/notice locations, root/core Cargo manifests or README declarations of either source. Upstream vendoring/redistribution clearance remains unresolved. This build adds an independently written Python contract checker and a local probe that includes pinned source in place. It does not copy the upstream core or integrate its full dependency tree as the production kernel.

## Canonical layout

Integers are unsigned big-endian; identifiers are exactly 32 bytes. The stored ID is not included in its own hash input. The outer storage envelope declares record family and format.

| Primitive | Canonical fields, in order |
|---|---|
| Object | `01`, type ID, definition ID, schema ID, u64 payload length, payload |
| Relation | `01`, source Object ID, relation-type ID, target Object ID, ordering flag; optional u64 ordering, u64 context length, context |
| Derivation | `01`, execution-class byte, u64 input count, typed inputs, operation ID, rule ID, u32 rule version, u64 parameter length, parameters, u64 output count, typed outputs |

Ordering flags are exactly 0/1. Execution classes are 0 deterministic and 1 attested. Each input/output is a 0 Object or 1 Relation tag followed by its 32-byte ID. An attested tag alone is not cryptographic evidence or a validity proof.

Identity is SHA-256 of the family-specific ASCII domain tag concatenated with canonical bytes:
`SILICATE_OBJECT_V1`, `SILICATE_RELATION_V1`, or `SILICATE_DERIVATION_V1`.
The protocol byte already occurs in the canonical bytes; do not insert it twice.
SHA3/V2 is outside this selected identity profile.

The reference checker consumes the complete record, rejects invalid flags, trailing bytes, truncated or impossible lengths/counts, enforces 1 MiB records and at most 4,096 references, and verifies a supplied claimed identity. These are explicit bounded-profile restrictions. The upstream low-level decoder returns a consumed length and its Relation decoder treats non-1 ordering flags as absent; the strict checker deliberately rejects those noncanonical inputs while preserving valid canonical bytes and IDs.

## Order and definitions

Sequence identity must commit to child order and repetitions in the Object payload. The M0 engineering sequence-payload convention is `u64 count` followed by ordered 32-byte child IDs. External membership Relations alone cannot redefine a sequence under an unchanged Object ID. [M1.2](UNICODE_SEQUENCES.md) now registers this convention for bounded Unicode scalar sequences, with exact byte spans and replay of the ordered membership Relations. General nested/learned sequence types remain later work.

Derivation input order is preserved; parameter bytes and rule version affect identity. Operation application direction must be explicitly defined by the operation contract. A hash-valid receipt records what is claimed; replay and domain validity need independent checks.

## Verification and dependencies

Seven [golden records](../fixtures/silicate-v1/golden.json) were generated by the actual pinned Rust encoders and identity functions: empty/scalar Objects, Relations with no/zero/maximum ordering, and deterministic/attested mixed-reference Derivations. The independently written [Python checker](../tools/silicate_contract.py) matches their bytes and IDs. Tests exercise malformed data, order, repeated children, nested-reference boundaries and fresh-process verification.

From the project root:

```sh
uv run --locked python -m pytest -q tests/test_silicate_contract.py
uv run --locked python -m tools.verify_contract
uv run --locked python -m tools.verify_contract --source-oracle
```

The last command requires the pinned local source paths and Rust toolchain. It checks source hashes/revision and the probe lock before running. The Python fixture checks can run without those source directories. The probe uses cached, locked `sha2=0.10.9` and `sha3=0.10.9`, with twelve resolved dependencies documented in [silicate-probe-dependencies.json](../manifests/silicate-probe-dependencies.json). All expose license metadata. These are local probe dependencies, not a decision to import the full Scratch core's PQ-crypto modules.

One bounded OpenAI development review found no material issue in the supplied codec. The source oracle and local tests establish the reported compatibility, independently of that review. No learner data or mastery evidence was generated.

At M0.1 completion, the production Rust kernel, complete registry/domain validation, operation executor and remaining M0 contracts were still pending; the approved M1.1 slice subsequently built the first Unicode Objects on this pinned format.

**Subsequent completion:** M1.1 created the initial Unicode collection, and [M0.2](ACTIVE_OBJECTS.md) added a bounded Python operation executor, finite registry extension and replay for scoped atom/group interactions. The production Rust kernel and general domain interpreter remain pending.

**Binary foundation, M0.3:** [native binary observations and local codes](BINARY_FOUNDATION.md) now use the same three canonical primitive families. Pattern-concept identity commits to scope and exact bits; replaceable codebooks map local codes to those immutable IDs. The new profile, lossless codecs and evaluation receipts do not reinterpret existing Unicode or active-object records.
