# M0.3 binary-foundation demonstrations

Created **30 October 2026**. These are engineering experiments with `learner_ingestion_allowed: false`. They do not contain pretrained knowledge or demonstrate semantic mastery or subjective experience.

| Artifact | Records | Purpose |
|---|---|---|
| [Native records](native/records.bin), [report](native/report.json), [manifest](native/manifest.json) | 194 Objects, 46 Relations, 6 Derivations | Discover scoped patterns from periodic native bits, optimize local codes, reconstruct and evaluate next-bit predictions |
| [M0.2 adapter records](active-atom-a/records.bin), [report](active-atom-a/report.json), [manifest](active-atom-a/manifest.json) | 131 Objects, 37 Relations, 6 Derivations | Read one active instance's committed history without changing it or pooling group/member experience |

`records.bin` contains canonical bytes and IDs for the three primitive families. `report.json` is a build snapshot; `manifest.json` pins the files and implementation hashes. Each artifact is immutable; a new run must use a new destination. The [format and operating guide](../../../../docs/BINARY_FOUNDATION.md) explains the binary layouts, concepts, codebooks, objective boundaries and commands. The [verification receipt](../../../../manifests/m0-3-verification.json) records tests and reproduction.

The native example reduces training representation from 44,928 to 39,880 bits including dictionary and framing. Its held-out next-bit errors are 2,049 versus 4,098 for the majority baseline. Charging the entire dictionary to the smaller holdout batch produces 21,800 bits versus 15,072 raw, so the measured storage benefit is not universal. The complete audit archive also retains all sources and search candidates and is larger than either selected representation.

The adapter selects raw representation and records 2 next-bit errors, equal to its majority baseline. It preserves original evidence roots, including an observation explicitly forwarded into atom A. It leaves the [M0.2 store](../../active-objects/m0-2/README.md) unchanged.

From the project root:

```sh
uv run --locked python -m tools.binary_language verify
uv run --locked python -m tools.binary_language inspect
uv run --locked python -m tools.binary_language verify \
  --directory data/experiments/binary-language/m0-3/active-atom-a
```
