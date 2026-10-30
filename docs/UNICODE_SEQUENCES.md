# M1.2 Unicode sequences: implemented contract

## Scope and status

M1.2 is a bounded, deterministic engineering envelope over Unicode 18 scalar Objects. It persists exactly three Silicate primitives: **Object, Relation, Derivation**. Object kinds and operation descriptors are not additional primitives. M0.3 native bits are unaffected.

Implementation: [contract](../tools/sequence_contract.py), [engine](../tools/sequence_engine.py), [persistence and CLI](../tools/unicode_sequences.py). See also [M1.2 proposal](M1_2_PROPOSAL.md).

These artifacts, all developer fixtures, and the `letter` demo are excluded from learner ingestion. No English meaning, active group, learning, or Neo4j integration is implemented. The local learner has no pretrained model; its permitted starting material remains Unicode 18 Objects, Silicate primitives, teacher seeds, approved dictionaries, and independently checked experience. External API output is development-only—not teacher seeds, training examples, learner responses, factual ground truth, or mastery assessments. A fixture supplying vocabulary, subject knowledge, or evaluation answers must not silently become learner input.

Completed **30 October 2026** under explicit approval. The development API authored the modules, tests and initial guide; Codex inspected the proposals, requested corrections, applied reviewed changes and ran local verification. **170 tests pass: 67 new checks and 103 existing checks.** Ruff and dependency checks also pass. Four saved artifacts reproduce byte-for-byte in separate processes. See the [verification receipt](../manifests/m1-2-verification.json) and [demonstration guide](../data/objects/sequences/m1-2/README.md). These results verify the engineering contract; they do not demonstrate language learning or mastery.

## Public interfaces

- `build(data: bytes, *, use_collection=True) -> (Bundle, report)` requires exact `bytes`, preserves the source, and performs structural validation. Normal construction checks accepted scalar Objects against the existing Unicode Collection.
- `build_text(text: str) -> (Bundle, report)` remains public in `sequence_engine`; it need not be re-exported by the CLI module. It requires exact `str` and strict UTF-8 encoding. A surrogate-containing string raises `ContractError`: no strict-UTF-8 original byte source exists to preserve.
- `verify_bundle(bundle) -> report` structurally validates, rebuilds from the sole source Object with `use_collection=False`, and requires byte-for-byte equality of canonical packs. Extra, missing, or altered records fail replay.
- `reconstruct(bundle) -> bytes` fully verifies, then reconstructs accepted input from ordered scalar children and compares it with the preserved source. Rejected input cannot use this reconstruction path.
- `Bundle.add`, `pack`, `from_bytes`, and `validate` manage the bounded canonical envelope. `validate()` alone is **not** semantic replay.
- Persistence exposes `publish`, `load`, `verify_directory`, and `reindex`. `read_bounded` must reject non-exact integers, negatives, and budgets above `MAX_PACK_BYTES` before opening a file.

## Tokenization and bounds

Tokenization strictly decodes UTF-8 and emits one token per supported Unicode scalar: deterministic Unicode scalar tokenization, **not a trained Unigram tokenizer or a learned subword vocabulary**. Scalars are not grapheme clusters. No normalization, case folding, replacement decoding, or newline conversion occurs. Combining marks and multi-scalar emoji remain separate scalar positions. Any future segmentation policy requires an explicit version.

Source bytes are limited to 4,096; accepted sequences to 1,024 scalars; bundles to 4,096 records and 2 MiB. Individual records also obey Silicate `MAX_RECORD_BYTES`. JSON artifact reads are limited to 262,144 bytes. Directory enumeration is bounded to the five required names plus optional `README.md`, rather than collecting arbitrary directory contents first.

Within the source-byte limit, rejection precedence is malformed UTF-8, scalar count, then unsupported repertoire scalar. Rejection preserves the exact source Object and emits a rejected result and Derivation, with no partial sequence, span map, scalar-member Relations, or scalar outputs. Oversized source bytes fail at the API boundary instead of creating a rejected artifact. Collection lookup starts only after all input checks pass.

`repertoire()` verifies `ucd/UnicodeData.txt` beneath `unicode_objects.UCD_ROOT` against SHA-256 `0736451de439ae7baf1425136617da495e09ee5afbe6e394374db7009ea08950`, expands assigned ranges, and filters valid scalars. Its cached result assumes the pinned input stays unchanged for the process lifetime; clear the cache or restart after changing it. The Unicode source is read-only. Detached accepted-input replay needs the pinned UCD, but not the original Collection SQLite database; malformed-UTF-8 and scalar-limit rejection replay can finish before repertoire loading.

## Objects, schemas, and identity

Every Object has type, definition, and schema handles plus a byte payload. Local handles are SHA-256 of `PROFILE:role:kind`, where the profile is `sovereign-unicode-sequence-v1`. Roles are `type`, `definition`, and `schema`. The registry incorporates the existing Unicode declarations and adds declaration Objects for every local kind/role. These engineering declarations are not vocabulary or subject facts.

Local kinds and payloads:

- `declaration`: canonical JSON `{role,name,handle,spec}`.
- `source-bytes`: exact input bytes.
- `sequence`: unsigned 64-bit big-endian count followed by ordered 32-byte scalar Object IDs.
- `span-map`: canonical JSON `{source,sequence,positions}`. Each position has `{index,byte_start,byte_end,scalar,object}`; offsets are half-open byte intervals and indexes are zero-based.
- `result`: `{profile,status,source,sequence,span_map,error,unicode_source_sha256}`. Rejected sequence/span references are null. Errors contain `code`, `byte_start`, `byte_end`, `scalar_index`, and optionally a formatted `scalar`.
- `operation`: `{name:"tokenize-compose",profile}`.
- `rule`: `{name:"strict-utf8-assigned-scalars",version:1,unicode_source_sha256}`.
- `relation-type`: `{name:"ordered-member",profile}`.

Unicode scalar Objects retain their existing Unicode bindings and four-byte big-endian scalar payload. Names and Unicode properties are not copied into artifacts. JSON payloads use sorted keys, compact separators, ASCII escaping, and no nonfinite numbers.

An ordered-member Relation links the sequence to a scalar Object, using the position as its ordering field and an empty context. Repeated scalars reuse the same Object but occupy distinct ordered positions. The deterministic Derivation references the source followed by scalar inputs in order, commits operation/rule/version/profile parameters, and outputs sequence, span map, result, then membership Relations. Rejection outputs only the result.

With fixed declarations, profile, and repertoire, identical content yields stable identities and canonical bytes. Changing scalar order changes the sequence identity and dependent records; pack sorting does not erase sequence order.

## Pack and persistence

`records.bin` starts with `SOVSEQ1\n`, then a four-byte big-endian record count. Each frame is:

`family-tag:u8 | ID:32 bytes | wire-length:u32 big-endian | canonical Silicate wire bytes`

Tags are 0 Object, 1 Relation, 2 Derivation. Frames are strictly sorted by ID. Duplicate/unsorted IDs, unknown tags, invalid identities, oversized or incomplete frames, and trailing bytes are rejected. Primitive wire encodings and identities remain those of the existing Silicate contract; no canonical schema is changed here.

Default directory: `data/objects/sequences/m1-2/letter`.

Required files are `records.bin`, `registry.json`, `report.json`, `manifest.json`, and `index.sqlite`; only `README.md` is additionally allowed. Artifact directory/file symlinks are rejected. This is a local filesystem contract, not a claim of protection against hostile concurrent path replacement.

The manifest contains `{format,profile,files,learner_ingestion_allowed:false}`. `files` commits SHA-256 and byte length for `records.bin`, `registry.json`, and `report.json`. JSON files are canonical JSON plus one newline. The replay-derived report includes status, IDs, counts, error, canonical pack hash, and `learner_ingestion_allowed:false`.

The rebuildable SQLite index has table `records(id BLOB PRIMARY KEY, family TEXT NOT NULL, offset INTEGER NOT NULL, wire_length INTEGER NOT NULL)`. Offsets point to frame starts; lengths describe primitive wire bytes. Lookup opens SQLite read-only, checks integrity and bounded rows against the canonical pack. The index is not manifest-authoritative. `reindex` verifies committed artifacts without trusting the index, then atomically replaces the index; it can recover a missing or corrupt regular index, but rejects symlinks.

Publication uses an exclusive sibling `.lock`, a sibling `.stage-*` directory, file/directory synchronization, validation, and rename to a previously absent destination. All publishers must follow the same locking protocol. Hard exits can leave locks and staging directories; review these manually before cleanup and retry. There is no automatic lock bypass. A post-publication hard exit can leave a valid destination and stale lock.

## CLI

Run from the repository root. Every subcommand accepts `--directory`:

- `tokenize --input PATH` and `compose --input PATH` are equivalent complete builds and publications.
- `inspect [--id HEX_ID]` shows the report/spans/source representation or one record.
- `verify` performs full directory verification.
- `reconstruct --output PATH [--source-only]` creates a new output file. Normally it reconstructs accepted scalars; `--source-only` exports preserved bytes, including rejected input, after verification.
- `reindex` rebuilds the lookup.
- `demo` publishes the development-only `b"letter"` fixture.

Use a fresh workspace and new destinations; publication and reconstruction refuse existing destinations:

```sh
work=$(mktemp -d)
.venv/bin/python -m tools.unicode_sequences demo --directory "$work/demo"
.venv/bin/python -m tools.unicode_sequences inspect --directory "$work/demo"
.venv/bin/python -m tools.unicode_sequences verify --directory "$work/demo"
.venv/bin/python -m tools.unicode_sequences reconstruct --directory "$work/demo" --output "$work/restored.bin"
.venv/bin/python -m tools.unicode_sequences reindex --directory "$work/demo"
.venv/bin/python -m tools.unicode_sequences tokenize --input "$work/restored.bin" --directory "$work/tokenized"
.venv/bin/python -m tools.unicode_sequences compose --input "$work/restored.bin" --directory "$work/composed"
```

Build commands return 0 for acceptance, 2 for a published rejection, and 1 for handled errors. Argument-parser usage errors also return 2; inspect the output to distinguish them from a saved rejected artifact. Source-derived output and error text are escaped. Tests cover invariants, persistence, CLI, hard exits, invalid read budgets and bounded directory enumeration.

## Development API provenance

Nine explicit bounded `gpt-6.1-sol` requests used 60,566 tokens: 42,007 input and 18,559 output. Requests retained the existing helper's input/output/time limits, no automatic retries, and development-only storage. Inspected corrections covered module names, recovery without an existing index, streaming source hashing, test field names, lint and resource bounds. Codex also corrected the guide's mistaken Unigram label and Relation field terminology. Local tests, independent reconstruction and artifact checks establish the verification result; API responses are not an authoritative grader.
