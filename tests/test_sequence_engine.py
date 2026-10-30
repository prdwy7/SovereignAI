"""Engineering-only fixtures: no learner ingestion, English claims, or mastery claims.

Proposed tests, not executed results. Only existing local data is used. The pinned
repertoire input is trusted to remain unchanged for its cached process lifetime.
"""

import dataclasses as dc
import json
import os
import subprocess
import sys

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tools import sequence_contract as c
from tools import sequence_engine as e
from tools import unicode_objects as u
from tools.silicate_contract import (
    ContractError,
    Derivation,
    Object,
    Relation,
    identity,
)


def build(data):
    return e.build(data, use_collection=False)


def record(bundle, report, key):
    return bundle.records[bytes.fromhex(report[key])]


def positions(bundle, report):
    return json.loads(record(bundle, report, "span_map_id").payload)["positions"]


def replace_record(bundle, old, new):
    """Repair primitive references and Derivation references, not domain JSON."""
    changes = {identity(old): identity(new)}
    del bundle.records[identity(old)]
    bundle.add(new)
    for key, rel in list(bundle.records.items()):
        if isinstance(rel, Relation):
            updated = dc.replace(
                rel,
                source=changes.get(rel.source, rel.source),
                target=changes.get(rel.target, rel.target),
                relation_type=changes.get(rel.relation_type, rel.relation_type),
            )
            if updated != rel:
                del bundle.records[key]
                changes[key] = bundle.add(updated)
    for key, deriv in list(bundle.records.items()):
        if isinstance(deriv, Derivation):
            updated = dc.replace(
                deriv,
                inputs=tuple(
                    dc.replace(r, identity=changes.get(r.identity, r.identity))
                    for r in deriv.inputs
                ),
                outputs=tuple(
                    dc.replace(r, identity=changes.get(r.identity, r.identity))
                    for r in deriv.outputs
                ),
                operation=changes.get(deriv.operation, deriv.operation),
                rule=changes.get(deriv.rule, deriv.rule),
            )
            del bundle.records[key]
            bundle.add(updated)


def replay_rejects(bundle):
    bundle.validate()
    with pytest.raises(ContractError):
        e.verify_bundle(bundle)


def test_letter_contract():
    b, r = e.build(b"letter")
    ids = [
        bytes.fromhex(u.inspect(u.DEFAULT_DESTINATION, ord(ch))["id"])
        for ch in ("l", "e", "t", "t", "e", "r")
    ]
    assert (r["scalar_count"], r["unique_scalar_count"]) == (6, 4)
    assert record(b, r, "sequence_id").payload == (b"\0\0\0\0\0\0\0\x06" + b"".join(ids))
    rels = sorted(
        (x for x in b.records.values() if isinstance(x, Relation)), key=lambda x: x.ordering
    )
    assert [x.ordering for x in rels] == list(range(6))
    assert [x.target for x in rels] == ids
    assert all(x.source == bytes.fromhex(r["sequence_id"]) for x in rels)
    assert all(x.context == b"" for x in rels)
    d = record(b, r, "derivation_id")
    assert d.rule_version == 1
    assert [x.kind for x in d.inputs] == ["object"] * 7
    assert [x.identity for x in d.inputs] == [bytes.fromhex(r["source_id"]), *ids]
    assert [x.kind for x in d.outputs] == ["object"] * 3 + ["relation"] * 6
    assert [x.identity for x in d.outputs[:3]] == [
        bytes.fromhex(r[k]) for k in ("sequence_id", "span_map_id", "result_id")
    ]
    assert [x.identity for x in d.outputs[3:]] == [identity(x) for x in rels]
    for role, entries in c.REGISTRY["maps"].items():
        for handle, target in entries.items():
            declaration = json.loads(b.records[bytes.fromhex(target)].payload)
            assert declaration["role"] == role
            assert declaration["handle"] == handle
    assert all(b.records[identity(x)] == x for x in c.DECLARATIONS)
    assert r["learner_ingestion_allowed"] is False
    b.validate()


def test_manual_utf8_intervals():
    data = "Aé😀e\u0301".encode()
    b, r = build(data)
    p = positions(b, r)
    assert [(x["byte_start"], x["byte_end"]) for x in p] == [
        (0, 1),
        (1, 3),
        (3, 7),
        (7, 8),
        (8, 10),
    ]
    assert [x["scalar"] for x in p] == [65, 233, 128512, 101, 769]
    assert e.reconstruct(b) == data


@pytest.mark.parametrize(
    "text",
    [
        "",
        "\0\t\r\n",
        "\ufeff",
        "\u202a\u202e\u202c\u2066\u2069",
        "\ue000",
        "\U000f0000",
        "😀",
        "👩\u200d💻",
        "e\u0301",
        "é",
        "\u0558",
    ],
)
def test_inputs(text):
    b, r = build(text.encode())
    assert r["status"] == "accepted"
    assert e.reconstruct(b) == text.encode()
    assert r["scalar_count"] == len(text)


def test_0558_in_pinned_derived_age():
    # Do not substitute the host Python unicodedata repertoire.
    path = u.UCD_ROOT / "ucd/DerivedAge.txt"
    found = False
    for line in path.read_text(encoding="utf-8").splitlines():
        body = line.split("#", 1)[0].strip()
        if not body:
            continue
        field, age = (x.strip() for x in body.split(";"))
        bounds = field.split("..")
        if int(bounds[0], 16) <= 0x558 <= int(bounds[-1], 16):
            assert age == "18.0"
            found = True
    assert found
    assert build("\u0558".encode())[1]["status"] == "accepted"


def test_identity_and_process_stability():
    reports = [build(x)[1] for x in (b"ab", b"ba", b"aa", b"a")]
    assert len({r["sequence_id"] for r in reports}) == 4
    assert build("é".encode())[1]["sequence_id"] != build("e\u0301".encode())[1]["sequence_id"]
    b, r = build(b"ab")
    assert build(b"ab")[0].pack() == b.pack()
    script = (
        "from tools.sequence_engine import build;"
        "print(build(b'ab',use_collection=False)[1]['canonical_sha256'])"
    )
    output = subprocess.check_output(
        [sys.executable, "-c", script], env=os.environ.copy(), text=True
    )
    assert output.strip() == r["canonical_sha256"]


@settings(max_examples=40, deadline=None)
@given(st.text(alphabet=list("aé😀e\u0301\0\t\r\n\u202e\ue000"), max_size=32))
def test_partition_property(text):
    data = text.encode()
    b, r = build(data)
    assert r["status"] == "accepted"
    assert e.reconstruct(b) == data
    offset = 0
    p = positions(b, r)
    assert len(p) == len(text)
    for i, (entry, char) in enumerate(zip(p, text, strict=True)):
        assert entry["index"] == i
        assert entry["byte_start"] == offset
        offset += len(char.encode())
        assert entry["byte_end"] == offset
        assert data[entry["byte_start"] : offset] == char.encode()
    assert offset == len(data)


@pytest.mark.parametrize(
    "bad,start,end",
    [
        (b"\xc0\xaf", 0, 1),
        (b"\xed\xa0\x80", 0, 1),
        (b"\xe2\x28\xa1", 0, 1),
        (b"\xf0\x9f\x98", 0, 3),
    ],
)
def test_malformed_atomic(bad, start, end):
    data = b"A" + bad
    b, r = build(data)
    assert r["error"] == dict(
        code="invalid-utf8", byte_start=start + 1, byte_end=end + 1, scalar_index=None
    )
    assert r["status"] == "rejected"
    assert r["sequence_id"] is None and r["span_map_id"] is None
    assert record(b, r, "source_id").payload == data
    assert not any(
        isinstance(x, Relation) or (isinstance(x, Object) and c.kind_of(x) == "unicode-scalar")
        for x in b.records.values()
    )
    e.verify_bundle(b)


@pytest.mark.parametrize("cp", [0x378, 0xFDD0, 0x10FFFF])
def test_unsupported(cp):
    b, r = build(b"A" + chr(cp).encode())
    assert r["error"] == dict(
        code="unsupported-scalar",
        byte_start=1,
        byte_end=1 + len(chr(cp).encode()),
        scalar_index=1,
        scalar=f"U+{cp:04X}",
    )
    assert r["sequence_id"] is None
    e.verify_bundle(b)


def test_limits_and_types(monkeypatch):
    assert build("😀".encode() * 1024)[1]["status"] == "accepted"
    assert build(b"a" * 1024)[1]["status"] == "accepted"
    r = build(b"a" * 1025)[1]
    assert r["error"] == dict(
        code="scalar-limit", byte_start=1024, byte_end=1025, scalar_index=1024
    )

    def forbidden():
        pytest.fail("byte limit must precede repertoire parsing")

    with monkeypatch.context() as m:
        m.setattr(e, "repertoire", forbidden)
        with pytest.raises(ContractError):
            build(b"a" * 4097)
    for value in ("a", bytearray(b"a"), memoryview(b"a"), None, 1):
        with pytest.raises(ContractError):
            e.build(value)
    for value in (b"a", None, 1, "\ud800", "\udfff", "a" * 4097):
        with pytest.raises(ContractError):
            e.build_text(value)
    for flag in (0, 1, None, "yes"):
        with pytest.raises(ContractError):
            e.build(b"a", use_collection=flag)


def test_collection_integrity(monkeypatch):
    a, _ = e.build(b"ab")
    b, _ = build(b"ab")
    assert a.pack() == b.pack()
    actual = u.inspect(u.DEFAULT_DESTINATION, 65)
    monkeypatch.setattr(u, "inspect", lambda *args: {**actual, "id": "00" * 32})
    with pytest.raises(ContractError, match="Collection"):
        e.build(b"A")
    assert build("\u0378".encode())[1]["status"] == "rejected"


def test_structural_negatives():
    b, r = build(b"ab")
    source = record(b, r, "source_id")
    b.add(dc.replace(source, definition=c.handle("definition", "sequence")))
    with pytest.raises(ContractError):
        b.validate()
    b, _ = build(b"a")
    del b.records[identity(c.DECLARATIONS[0])]
    with pytest.raises(ContractError):
        b.validate()
    b, r = build(b"a")
    del b.records[bytes.fromhex(r["source_id"])]
    with pytest.raises(ContractError):
        b.validate()


def test_frame_negatives():
    b, _ = build(b"a")
    wire = b.pack()
    base = len(c.MAGIC) + 4
    frames = []
    pos = base
    while pos < len(wire):
        end = pos + 37 + int.from_bytes(wire[pos + 33 : pos + 37], "big")
        frames.append(wire[pos:end])
        pos = end
    header = c.MAGIC

    def pack(parts):
        return header + len(parts).to_bytes(4, "big") + b"".join(parts)

    bad_tag = bytearray(wire)
    bad_tag[base] = 255
    bad_id = bytearray(wire)
    bad_id[base + 1] ^= 1
    bad_length = bytearray(wire)
    bad_length[base + 33 : base + 37] = (c.MAX_RECORD_BYTES + 1).to_bytes(4, "big")
    invalid = [
        bytes(bad_tag),
        bytes(bad_id),
        bytes(bad_length),
        wire + b"\0",
        wire[:-1],
        b"X" + wire[1:],
        pack([frames[0], frames[0]]),
        pack(list(reversed(frames))),
        header + (c.MAX_RECORDS + 1).to_bytes(4, "big"),
    ]
    assert c.Bundle.from_bytes(wire).pack() == wire
    for data in invalid:
        with pytest.raises(ContractError):
            c.Bundle.from_bytes(data)


@pytest.mark.parametrize("tamper", ["extra", "span", "relation", "sequence"])
def test_full_replay_semantic_negatives(tamper):
    b, r = build(b"ab")
    if tamper == "extra":
        b.add(c.obj("source-bytes", b"engineering-only"))
    elif tamper == "span":
        old = record(b, r, "span_map_id")
        value = json.loads(old.payload)
        value["positions"][0]["byte_end"] = 2
        replace_record(b, old, c.jobj("span-map", value))
    elif tamper == "relation":
        old = next(x for x in b.records.values() if isinstance(x, Relation))
        replace_record(b, old, dc.replace(old, ordering=99))
    else:
        old = record(b, r, "sequence_id")
        payload = old.payload
        replace_record(
            b, old, dc.replace(old, payload=payload[:8] + payload[40:72] + payload[8:40])
        )
    replay_rejects(b)
