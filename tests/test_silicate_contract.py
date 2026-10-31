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
"""M0.1 contract checks against independent Rust golden vectors and malformed inputs."""

import hashlib
import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tools.silicate_contract import (
    DOMAINS,
    MAX_RECORD_BYTES,
    ContractError,
    Derivation,
    Object,
    Reference,
    Relation,
    decode,
    encode,
    identity,
    ordered_payload,
)

ROOT = Path(__file__).resolve().parent.parent
VECTORS = json.loads((ROOT / "fixtures/silicate-v1/golden.json").read_text())["vectors"]


@pytest.mark.parametrize("vector", VECTORS, ids=[v["name"] for v in VECTORS])
def test_matches_rust_source_golden_bytes_and_ids(vector):
    wire = bytes.fromhex(vector["canonical_hex"])
    record = decode(vector["kind"], wire, bytes.fromhex(vector["id_hex"]))
    assert encode(record) == wire
    assert identity(record).hex() == vector["id_hex"]


@pytest.mark.parametrize("vector", VECTORS, ids=[v["name"] for v in VECTORS])
def test_all_truncated_prefixes_and_trailing_bytes_rejected(vector):
    wire = bytes.fromhex(vector["canonical_hex"])
    for length in range(len(wire)):
        with pytest.raises(ContractError):
            decode(vector["kind"], wire[:length])
    with pytest.raises(ContractError):
        decode(vector["kind"], wire + b"\x00")


def test_noncanonical_flags_and_excessive_counts_rejected():
    relation = bytearray.fromhex(VECTORS[2]["canonical_hex"])
    relation[97] = 2
    with pytest.raises(ContractError, match="ordering tag"):
        decode("relation", bytes(relation))
    derivation = bytearray.fromhex(VECTORS[5]["canonical_hex"])
    for offset in (0, 1, 10):  # protocol, execution class, first reference tag
        invalid = derivation.copy()
        invalid[offset] = 7
        with pytest.raises(ContractError):
            decode("derivation", bytes(invalid))
    derivation[2:10] = b"\xff" * 8
    with pytest.raises(ContractError, match="reference count"):
        decode("derivation", bytes(derivation))


def test_identity_mismatch_and_domain_separation():
    vector = VECTORS[0]
    wire = bytes.fromhex(vector["canonical_hex"])
    with pytest.raises(ContractError, match="identity mismatch"):
        decode("object", wire, bytes(32))
    assert len({hashlib.sha256(domain + wire).digest() for domain in DOMAINS.values()}) == 3


def test_repeated_children_and_program_order_remain_distinct():
    a, b = bytes([10]) * 32, bytes([11]) * 32
    base = Object(bytes(32), bytes(32), bytes(32), ordered_payload((a, b, a)))
    assert identity(base) != identity(replace(base, payload=ordered_payload((a, a, b))))
    assert identity(base) != identity(replace(base, payload=ordered_payload((a, b))))
    program = Derivation(
        "deterministic", (Reference("object", a), Reference("object", b)), a, b, 1, b"", ()
    )
    assert identity(program) != identity(replace(program, inputs=tuple(reversed(program.inputs))))
    assert identity(Relation(a, b, a, None, b"")) != identity(Relation(a, b, a, 0, b""))


def test_nested_reference_is_not_a_fourth_primitive():
    ref = Reference("object", bytes(32))
    with pytest.raises(ContractError, match="Unknown record family"):
        encode(ref)
    with pytest.raises(ContractError, match="Unknown record family"):
        decode("reference", bytes(32))
    record = Derivation("deterministic", (ref,), bytes(32), bytes(32), 1, b"", ())
    assert decode("derivation", encode(record), identity(record)) == record


@pytest.mark.parametrize("ordering", [-1, 1 << 64, True])
def test_invalid_numeric_fields_rejected(ordering):
    with pytest.raises(ContractError):
        encode(Relation(bytes(32), bytes(32), bytes(32), ordering, b""))


def test_wrong_width_oversize_and_reference_family_rejected():
    with pytest.raises(ContractError):
        encode(Object(bytes(31), bytes(32), bytes(32), b""))
    with pytest.raises(ContractError):
        decode("object", b"\x01" * (MAX_RECORD_BYTES + 1))
    with pytest.raises(ContractError):
        encode(
            Derivation(
                "deterministic",
                (Reference("derivation", bytes(32)),),
                bytes(32),
                bytes(32),
                1,
                b"",
                (),
            )
        )
    with pytest.raises(ContractError):
        decode("unknown", b"")


@given(st.binary(max_size=256))
@settings(max_examples=100, derandomize=True, deadline=None)
def test_payload_roundtrip_without_interpretation(payload):
    record = Object(bytes([1]) * 32, bytes([2]) * 32, bytes([3]) * 32, payload)
    assert decode("object", encode(record), identity(record)) == record


@given(st.binary(max_size=256))
@settings(max_examples=100, derandomize=True, deadline=None)
def test_arbitrary_bytes_fail_cleanly_or_are_canonical(wire):
    for kind in DOMAINS:
        try:
            result = decode(kind, wire)
        except ContractError:
            continue
        assert encode(result) == wire


def test_fresh_process_verifies_same_fixtures():
    result = subprocess.run(
        [sys.executable, "-m", "tools.verify_contract"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert json.loads(result.stdout)["vectors_verified"] == len(VECTORS)
