# Copyright (C) 2020 Pridhvi Patagarla
#
# SovereignAI is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation, version 3 of the License.
#
# SovereignAI is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SovereignAI.  If not, see <https://www.gnu.org/licenses/>.
#
"""Engineering fixtures only: scope, executable contracts, persistence and recovery."""

import json
import subprocess
import sys

import pytest

from tools.active_objects import (
    BOOTSTRAP_RECORDS,
    REGISTRY_MAPS,
    ROOT,
    Store,
    demo,
    handle,
    obj,
    unpack,
)
from tools.silicate_contract import (
    PRIMITIVE_KINDS,
    ContractError,
    Derivation,
    Object,
    decode,
    encode,
    identity,
)


@pytest.fixture
def store(tmp_path):
    instance = Store.create(tmp_path / "records.sqlite", "test-run")
    yield instance
    instance.close()


def atom(store, name="a", scalar=0x41, **limits):
    store.submit(
        "atom",
        name=name,
        scalar=scalar,
        max_steps=limits.get("max_steps", 16),
        memory_limit=limits.get("memory_limit", 16),
    )
    return store.inspect(name)["id"]


def observe(store, instance, scalar=0x41, event="e1"):
    return store.submit("observe", instance=instance, scalar=scalar, event=event, source="fixture")


def group(store, a, b, name="ab"):
    store.submit("group", name=name, members=[a, b], max_steps=16, memory_limit=16)
    return store.inspect(name)["id"]


def permit(store, group_id, member):
    receipt = store.submit("allow_forward", group=group_id, member=member)
    return store.output(receipt, "policy")["id"]


def test_observation_history_identity_and_exactly_three_primitives(store):
    a = atom(store)
    results = [
        store.output(observe(store, a, cp, f"e{i}"), "result")["matched"]
        for i, cp in enumerate((0x41, 0x42, 0x41))
    ]
    assert results == [True, False, True]
    state = store.inspect("a")["state"]
    assert (state["observations"], state["matches"], len(state["memory"])) == (3, 2, 3)
    assert store.verify()["verified"]
    assert set(r[0] for r in store.db.execute("SELECT DISTINCT kind FROM records")) == set(
        PRIMITIVE_KINDS
    )
    for rid, kind, wire in store.db.execute("SELECT id,kind,wire FROM records"):
        record = decode(kind, wire, rid)
        assert encode(record) == wire
        if isinstance(record, Object):
            for role, value in zip(
                ("type", "definition", "schema"),
                (record.object_type, record.definition, record.schema),
                strict=True,
            ):
                assert isinstance(
                    store.get(bytes.fromhex(REGISTRY_MAPS[role][value.hex()])), Object
                )


def test_group_has_fresh_history_and_never_updates_members_implicitly(store):
    a, b = atom(store), atom(store, "b", 0x42)
    observe(store, a)
    before_a, before_b = store.inspect("a"), store.inspect("b")
    g = group(store, a, b)
    assert store.inspect("ab")["state"]["memory"] == []
    assert store.inspect("ab")["state"]["observations"] == 0
    outcomes = [
        store.output(observe(store, g, cp, f"g{i}"), "result")["matched"]
        for i, cp in enumerate((0x41, 0x42, 0x43))
    ]
    assert outcomes == [True, True, False]
    assert store.inspect("a") == before_a
    assert store.inspect("b") == before_b
    assert store.verify()["verified"]


def test_explicit_transfer_reinterprets_at_member_scope_and_preserves_origin(store):
    a, b = atom(store), atom(store, "b", 0x42)
    g = group(store, a, b)
    event = observe(store, g, 0x41)
    assert store.output(event, "result")["matched"] is True
    before_a, before_b, before_g = store.inspect("a"), store.inspect("b"), store.inspect("ab")
    policy = permit(store, g, b)
    assert permit(store, g, b) == policy
    assert store.inspect("b") == before_b  # A connection alone does not execute a transfer.
    forwarded = store.submit("forward", policy=policy, receipt=event)
    assert store.output(forwarded, "result")["matched"] is False  # A is not B.
    source = store.output(event, "observation")
    target = store.output(forwarded, "observation")
    assert target["origin"] == source["id"]
    assert target["root"] == source["root"]
    assert target["instance"] == b and source["instance"] == g
    assert target["policy"] == policy
    assert store.inspect("a") == before_a and store.inspect("ab") == before_g
    before_duplicate = store.snapshot()
    assert store.submit("forward", policy=policy, receipt=event) == forwarded
    assert store.snapshot() == before_duplicate
    assert store.verify()["verified"]


def test_event_idempotency_and_conflicting_reuse(store):
    a = atom(store)
    receipt = observe(store, a)
    before = store.snapshot()
    assert observe(store, a) == receipt
    assert store.snapshot() == before
    with pytest.raises(ContractError, match="different content"):
        observe(store, a, 0x42)
    assert store.snapshot() == before
    observe(store, a, event="e2")
    assert store.inspect("a")["state"]["observations"] == 2


def test_instances_of_same_symbol_keep_separate_histories(store):
    a, other = atom(store), atom(store, "other")
    assert a != other
    observe(store, a)
    assert store.inspect("other")["state"]["observations"] == 0
    observe(store, other)
    assert store.inspect("a")["state"]["memory"] != store.inspect("other")["state"]["memory"]


def test_policy_scope_and_missing_policy_rejected(store):
    a, b, c = atom(store), atom(store, "b", 0x42), atom(store, "c", 0x43)
    g = group(store, a, b)
    other_g = group(store, b, c, "bc")
    policy = permit(store, g, a)
    outside = observe(store, other_g)
    atom_event = observe(store, b)
    before = store.snapshot()
    for invalid_source in (outside, atom_event):
        with pytest.raises(ContractError, match="outside policy scope"):
            store.submit("forward", policy=policy, receipt=invalid_source)
    with pytest.raises(ContractError, match="Missing record"):
        store.submit("forward", policy="00" * 32, receipt=outside)
    with pytest.raises(ContractError, match="direct atomic member"):
        permit(store, g, c)
    assert store.snapshot() == before


def test_membership_commits_to_order_and_rejects_duplicate_nested_groups(store):
    a, b = atom(store), atom(store, "b", 0x42)
    g = group(store, a, b)
    reversed_group = group(store, b, a, "ba")
    assert g != reversed_group
    assert store.inspect("ab")["instance"]["members"] == [a, b]
    before = store.snapshot()
    for members in ([a, a], [a], [a, g]):
        with pytest.raises(ContractError):
            store.submit("group", name="bad", members=members, max_steps=16, memory_limit=16)
    assert store.snapshot() == before


@pytest.mark.parametrize(
    "limits,error", [({"max_steps": 1}, "Step"), ({"memory_limit": 1}, "Memory")]
)
def test_execution_limits_are_atomic(store, limits, error):
    a = atom(store, **limits)
    observe(store, a)
    before = store.snapshot()
    with pytest.raises(ContractError, match=error + " budget"):
        observe(store, a, event="e2")
    assert store.snapshot() == before


def test_command_limit_and_duplicate_at_limit(tmp_path):
    store = Store.create(tmp_path / "limits.sqlite", "limited", max_commands=2)
    try:
        a = atom(store)
        event = observe(store, a)
        assert observe(store, a) == event
        with pytest.raises(ContractError, match="Command budget"):
            observe(store, a, event="next")
        assert store.verify()["verified"]
    finally:
        store.close()


@pytest.mark.parametrize("scalar", [True, -1, 0xD800, 0x110000, 0x378])
def test_invalid_or_unassigned_symbols_fail_without_state_change(store, scalar):
    a = atom(store)
    before = store.snapshot()
    with pytest.raises(ContractError):
        observe(store, a, scalar)
    assert store.snapshot() == before


def test_unknown_rules_invalid_references_and_invalid_declarations(store):
    before = store.snapshot()
    with pytest.raises(ContractError, match="Unsupported operation"):
        store.submit("become_sentient")
    with pytest.raises(ContractError, match="Unknown active"):
        observe(store, "00" * 32)
    good = obj("operation", {"name": "atom", "version": 1})
    bad = Object(good.object_type, b"x" * 32, good.schema, good.payload)
    with pytest.raises(ContractError, match="Unresolved declaration"):
        store.put(bad)
    assert store.snapshot() == before


def test_exception_rolls_back_records_indexes_and_state(store):
    a = atom(store)
    before, state = store.snapshot(), store.inspect("a")

    def interrupt(_):
        raise RuntimeError("injected interruption")

    store.failpoint = interrupt
    with pytest.raises(RuntimeError, match="interruption"):
        observe(store, a)
    store.failpoint = None
    assert store.snapshot() == before and store.inspect("a") == state
    observe(store, a)
    assert store.verify()["verified"]


@pytest.mark.parametrize("phase", ["before_commit", "after_commit"])
def test_process_exit_at_commit_boundary_recovers_cleanly(tmp_path, phase):
    path = tmp_path / "crash.sqlite"
    store = Store.create(path, "crash")
    a = atom(store)
    before, state = store.snapshot(), store.inspect("a")
    store.close()
    script = """
import os, sys
from pathlib import Path
from tools.active_objects import Store
s = Store.open(Path(sys.argv[1]))
s.failpoint = lambda stage: os._exit(73) if stage == sys.argv[3] else None
s.submit('observe', instance=sys.argv[2], scalar=65, event='crash-event', source='fixture')
"""
    process = subprocess.run(
        [sys.executable, "-c", script, str(path), a, phase], check=False, timeout=20
    )
    assert process.returncode == 73
    recovered = Store.open(path)
    try:
        if phase == "before_commit":
            assert recovered.snapshot() == before and recovered.inspect("a") == state
        else:
            assert recovered.inspect("a")["state"]["observations"] == 1
        receipt = observe(recovered, a, event="crash-event")
        assert recovered.inspect("a")["state"]["observations"] == 1
        snapshot = recovered.snapshot()
        assert observe(recovered, a, event="crash-event") == receipt
        assert recovered.snapshot() == snapshot
        assert recovered.verify()["verified"]
    finally:
        recovered.close()


def test_replay_rejects_validly_hashed_but_unexecuted_state(store):
    atom(store)
    state = dict(store.inspect("a")["state"])
    state["observations"] = 9
    forged = obj("state", state)
    store.put(forged)
    store.db.execute("UPDATE instances SET state=? WHERE name='a'", (identity(forged),))
    with pytest.raises(ContractError, match="Replay record mismatch"):
        store.verify()


def test_replay_rejects_tampered_index(store):
    a, b = atom(store), atom(store, "b", 0x42)
    store.db.execute(
        "UPDATE instances SET state=? WHERE id=?",
        (bytes.fromhex(store.inspect("b")["state_id"]), bytes.fromhex(a)),
    )
    with pytest.raises(ContractError, match="Replay index mismatch"):
        store.verify()
    assert b != a


def test_receipt_verification_reexecutes_rule(store):
    a = atom(store)
    receipt_id = observe(store, a)
    receipt = store.get(bytes.fromhex(receipt_id))
    assert isinstance(receipt, Derivation)
    wrong = Derivation(
        receipt.execution_class,
        receipt.inputs,
        receipt.operation,
        receipt.rule,
        2,
        receipt.parameters,
        receipt.outputs,
    )
    store.put(wrong)
    with pytest.raises(ContractError, match="Unsupported receipt"):
        store.verify()


def test_schema_validation_and_bootstrap_resolution(store):
    for record in BOOTSTRAP_RECORDS:
        assert store.get(identity(record)) == record
    good = obj("operation", {"name": "atom", "version": 1})
    with pytest.raises(ContractError):
        unpack(Object(good.object_type, good.definition, handle("schema", "state"), good.payload))
    with pytest.raises(ContractError):
        obj("state", {"instance": "missing fields"})


def test_noncanonical_references_and_invalid_labels_are_rejected(store):
    a = atom(store)
    before = store.snapshot()
    with pytest.raises(ContractError, match="canonical"):
        observe(store, a.upper())
    with pytest.raises(ContractError, match="Labels"):
        atom(store, 17)
    assert store.snapshot() == before


def test_record_inspector_shows_object_bindings_and_derivation_references(store):
    a = atom(store)
    event = observe(store, a)
    instance = store.inspect_record(a)
    assert instance["kind"] == "object"
    assert set(instance["declarations"]) == {"type", "definition", "schema"}
    assert instance["decoded_payload"]["level"] == "atom"
    receipt = store.inspect_record(event)
    assert receipt["kind"] == "derivation"
    assert {reference["kind"] for reference in receipt["fields"]["outputs"]} == {
        "object",
        "relation",
    }


def test_independent_runs_match_and_demo_restart(tmp_path):
    first = demo(tmp_path / "first")
    second = demo(tmp_path / "second")
    assert first == second
    assert first["scope_isolation"] and first["restart_state_matches"]
    assert first["initial_group"]["state"]["observations"] == 0
    assert first["atom_before_group"]["state"]["observations"] == 3
    assert first["atom_after_group_events"]["state"]["observations"] == 3
    assert first["atom_after_explicit_transfer"]["state"]["observations"] == 4
    assert first["unaffected_member"]["state"]["observations"] == 0
    assert first["verification"]["learner_ingestion_allowed"] is False
    with pytest.raises(ContractError, match="already exists"):
        demo(tmp_path / "first")
    assert json.loads((tmp_path / "first/report.json").read_text()) == first
    golden = json.loads((ROOT / "fixtures/active-objects-v1/scoped-demo.json").read_text())
    assert first["verification"]["canonical_sha256"] == golden["canonical_sha256"]
    assert first["verification"]["counts"] == golden["counts"]
    for key, expected in golden["expected"].items():
        assert [first[key]["state"]["observations"], first[key]["state"]["matches"]] == expected
    for key in ("group_receipt", "transfer_policy", "transfer_receipt"):
        assert first[key] == golden[key]


def test_cli_apply_explicit_request_and_inspection(tmp_path):
    directory = tmp_path / "cli-demo"
    report = demo(directory)
    request = tmp_path / "request.json"
    request.write_text(
        json.dumps(
            {
                "action": "observe",
                "arguments": {
                    "instance": report["unaffected_member"]["id"],
                    "scalar": 0x42,
                    "event": "manual-1",
                    "source": "fixture",
                },
            }
        )
    )
    command = [sys.executable, "-m", "tools.active_objects"]
    result = subprocess.run(
        [*command, "apply", "--directory", str(directory), "--request", str(request)],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    assert json.loads(result.stdout)["verification"]["commands"] == 11
    inspected = subprocess.run(
        [*command, "inspect", "--directory", str(directory), "--name", "atom-b"],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    assert json.loads(inspected.stdout)["state"]["matches"] == 1
