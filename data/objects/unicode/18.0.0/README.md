# First-level Unicode 18.0 Objects

Build **M1.1**, completed **30 October 2026** after explicit user approval.

This collection contains **310,341 Unicode scalar Objects** and **6 engineering declaration Objects**, for **310,347 Objects total**. UnicodeData.txt First/Last ranges are expanded. All 2,048 surrogate code points are excluded. Assigned control and private-use scalar records are included; unassigned scalars are not materialized.

## Where every Object is stored

| File | Contents |
|---|---|
| [objects.bin](objects.bin) | All canonical Objects and their 32-byte content IDs; 45,001,384 bytes |
| [index.sqlite](index.sqlite) | Scalar/ID lookup to file offsets, plus separate infrastructure names/categories; 47,009,792 bytes |
| [registry.json](registry.json) | Typed type/definition/schema handles mapped to declaration Object IDs |
| [manifest.json](manifest.json) | Source hash/version, counts, file hashes, implementation hash and reproduction evidence |

There is one framed collection rather than a separate filesystem file per Object. The collection begins with `SOVOBJ1` plus a newline. Each frame is `u32 canonical-byte length || 32-byte Object ID || canonical bytes`. The index records the frame offset and canonical length. The six declaration Objects precede the scalar Objects, which are stored in increasing code-point order.

Canonical Object bytes follow the [pinned Silicate contract](../../../../docs/FOUNDATION_CONTRACT.md): protocol byte, 32-byte type handle, 32-byte definition handle, 32-byte schema handle, 64-bit payload length, then payload. A scalar Object's payload is exactly its four-byte unsigned big-endian scalar value.

## Definitions and the three primitives

The core has exactly **Object, Relation, Derivation**. This first collection stores Objects. Type/definition/schema declarations are also Objects; the registry and SQLite tables are lookup structures and do not add primitives.

The finite bootstrap profile defines declaration and Unicode-scalar object bindings. Each scalar Object resolves its type, definition and schema handle to a real declaration Object in the same collection. Each declaration Object itself has an explicit declaration type/definition/schema binding. The registry uses stable typed handles mapped to content IDs, so no Object needs to contain its own hash to define itself.

The bootstrap contract is an engineering foundation for this initial collection. It is not a general learned ontology, a schema interpreter loaded from arbitrary text, or a production implementation of the future full core.

## Inspect an Object

From the SovereignAI project root:

```sh
uv run --locked python -m tools.unicode_objects inspect --scalar U+0041
uv run --locked python -m tools.unicode_objects inspect --scalar U+1F600
```

For U+0041, the actual Object has:

```text
id:         424f0d305baadc1950fa10bc2405858b11db728c0277329b986658d9e839e3dc
type:       77a84f277454bd996e5aa5e8aa18a13072cfa66d58be908e92a68173a1b092ce
definition: cb295ef03e530b599a9ee92c7228ef7f5098ea2438712372383809bc66f9150a
schema:     e11cb9a09839dfa281e7b3cb18b26e99b34d77fdf85443a1885e615ea54fb617
payload:    00000041
```

The inspection command separately displays source name/category metadata. Names and numeric code-point values do not confer English or mathematical meanings on the learner. Word formation, grammar, grounding, Relations and Derivations are later approved work.

## Verify or reproduce

```sh
uv run --locked python -m tools.unicode_objects verify
uv run --locked python -m pytest -q tests
```

Full verification recomputes every Object ID, checks complete decoding, resolves all declarations, compares scalar coverage and infrastructure metadata against the source, checks the SQLite index, and verifies file hashes. Individual inspection verifies its returned Object/frame; use full verification to establish whole-collection integrity.

To reproduce without overwriting this collection, choose a new directory:

```sh
uv run --locked python -m tools.unicode_objects build --directory .cache/unicode-reproduction
```

The builder rejects an existing destination. It builds in a staging directory and publishes after verification. Interrupted/failed staging directories are not accepted collections. Canonical bytes, IDs, registry and record order are deterministic. Timestamps and SQLite byte layouts are environment-specific; compare canonical collection/registry hashes for reproducibility. An independent rebuild of this collection matched those hashes, and on this machine its index bytes also matched.

The [verification receipt](../../../../manifests/unicode-object-verification.json) records completion evidence. The [source data and license](../../../unicode/18.0.0/README.md) remain preserved. These files are a local object collection and import artifact; the planned Neo4j adapter is a later build.
