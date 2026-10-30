# M0.2 active-object demonstration

Engineering-only run, created **30 October 2026**. It contains scoped interaction histories, not language lessons or evidence of subjective experience. `learner_ingestion_allowed` is false.

| File | Contents |
|---|---|
| [records.sqlite](records.sqlite) | Canonical records: 99 Objects, 26 Relations, 10 Derivations; derived command, instance and idempotency indexes |
| [report.json](report.json) | Build snapshot: state histories, explicit transfer policy/receipt, scope isolation, replay and restart evidence |

The original 310,341 scalar Objects and six declarations remain in [the Unicode collection](../../../objects/unicode/18.0.0/README.md). This demonstration copies only its three referenced scalars and required declarations under unchanged IDs.

From the project root:

```sh
uv run --locked python -m tools.active_objects verify
uv run --locked python -m tools.active_objects inspect --name atom-a
uv run --locked python -m tools.active_objects inspect --name atom-b
uv run --locked python -m tools.active_objects inspect --name group-ab
```

The saved outcomes are:

| Point in the run | A observations / matches | B observations / matches | Group observations / matches |
|---|---|---|---|
| After A's own A, B, A events | 3 / 2 | 0 / 0 | Not yet created |
| After creating group AB | 3 / 2 | 0 / 0 | 0 / 0 |
| After the group's A, C events | 3 / 2 | 0 / 0 | 2 / 1 |
| After explicitly forwarding the group's A event to A | 4 / 3 | 0 / 0 | 2 / 1 |

Membership and forwarding authorization are distinct. A group starts a fresh scope; its events leave member states unchanged unless an explicit forwarding call is made. Forwarded evidence preserves its origin and does not become an independent witness. The transition's new state is a new Object; the original scalar Object is unchanged.

See [the contract and command guide](../../../../docs/ACTIVE_OBJECTS.md) and [verification receipt](../../../../manifests/m0-2-verification.json). The report describes the saved build snapshot; after applying more commands, use inspection and verification to read the current store.
