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
"""Engineering tests for binary representation, scope, provenance and held-out evaluation."""

import json
import subprocess
import sys
from collections import Counter
from dataclasses import replace

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from tools.active_objects import Store
from tools.binary_codec import (
    MAX_BITS,
    decode_tokens,
    encode_tokens,
    pack_bits,
    prefix_codes,
    segment,
    unpack_bits,
    validate_codes,
)
from tools.binary_language import (
    DECLARATIONS,
    DEFAULT_CONFIG,
    LINKS,
    REGISTRY_MAPS,
    ROOT,
    Bundle,
    Sample,
    build,
    concept,
    demo,
    digest,
    discover,
    engineering_samples,
    from_active,
    kind_of,
    make_book,
    object_record,
    parse_observation,
    publish,
    read_book,
    reconstruct,
    verify_bundle,
    verify_directory,
)
from tools.silicate_contract import ContractError, Object, Relation, encode, identity


def small(scope="scope", train=None, test=None):
    return build(
        scope,
        engineering_samples("train", train or ["01010101", "01010101"]),
        engineering_samples("test", test or ["0101011"]),
    )


def objects(bundle, kind):
    return [r for r in bundle.records.values() if isinstance(r, Object) and kind_of(r) == kind]


@given(st.text(alphabet="01", min_size=0, max_size=256))
@settings(max_examples=60)
def test_bit_packing_and_prefix_roundtrip(bits):
    assert unpack_bits(pack_bits(bits)) == bits
    patterns = ("0", "1", "00", "01", "10", "11", "101")
    tokens, _ = segment(bits, patterns)
    counts = Counter({pattern: 0 for pattern in patterns})
    counts.update(tokens)
    codes = prefix_codes(counts)
    encoded = encode_tokens(tokens, codes)
    assert decode_tokens(encoded, codes, len(bits), len(tokens))[0] == bits


@pytest.mark.parametrize(
    "payload",
    [b"", b"\0\0\0\1\x81", b"\0\0\0\0\0", b"\0\0\0\11\0", (MAX_BITS + 1).to_bytes(4, "big")],
)
def test_malformed_bit_packing(payload):
    with pytest.raises(ContractError):
        unpack_bits(payload)


@pytest.mark.parametrize(
    "codes",
    [
        {"0": "0", "1": "01"},
        {"0": "0", "1": "0"},
        {"0": "", "1": "1"},
        {"0": "0"},
        {"0": "2", "1": "1"},
    ],
)
def test_invalid_codebooks(codes):
    with pytest.raises(ContractError):
        validate_codes(codes)


def test_huffman_known_weighted_length_and_determinism():
    counts = Counter({"0": 45, "1": 13, "00": 12, "11": 5})
    codes = prefix_codes(counts)
    assert sum(counts[p] * len(code) for p, code in codes.items()) == 122
    assert codes == prefix_codes(Counter(dict(reversed(list(counts.items())))))
    with pytest.raises(ContractError):
        decode_tokens("0", {"0": "00", "1": "01"}, 1, 1)
    with pytest.raises(ContractError):
        decode_tokens("11", {"0": "0", "1": "1"}, 1, 1)


def test_tiny_inputs_select_raw_with_full_dictionary_cost():
    bundle, report = small()
    summary = report["summary"]
    assert summary["selected"] == "raw"
    raw = summary["candidates"][0]["measurements"]["bits"]
    assert raw == summary["representation"]["training_raw_bits"]
    assert all(candidate["measurements"]["bits"] > raw for candidate in summary["candidates"][1:])
    assert verify_bundle(bundle) == report


def test_repetition_can_justify_a_dictionary_and_improve_bounded_prediction():
    training = engineering_samples("long-train", ["00101101" * 256 for _ in range(12)])
    holdout = engineering_samples("long-test", ["00101101" * 255 + "00101"])
    bundle, report = build("periodic-fixture", training, holdout)
    summary = report["summary"]
    assert summary["selected"].startswith("prefix-")
    assert (
        summary["representation"]["training_selected_bits"]
        < summary["representation"]["training_raw_bits"]
    )
    assert summary["prediction"]["errors"] < summary["prediction"]["majority_baseline_errors"]
    assert summary["semantic_understanding"] == "not_established"
    assert summary["prediction"]["semantic_error"] is None
    for record in objects(bundle, "expression"):
        reconstruct(record, bundle)


def test_partial_bytes_empty_observations_and_zero_target_evaluation():
    bundle, report = small(train=["", "1"], test=[""])
    assert report["summary"]["prediction"]["targets"] == 0
    assert not report["summary"]["prediction"]["improved_over_majority"]
    assert verify_bundle(bundle) == report
    for record in objects(bundle, "expression"):
        assert reconstruct(record, bundle) in {"", "1"}


def test_three_primitives_and_every_object_declaration_resolves():
    bundle, _ = small()
    kinds = set()
    for record in bundle.records.values():
        kinds.add(type(record).__name__)
        if isinstance(record, Object):
            for role, key in zip(
                ("type", "definition", "schema"),
                (record.object_type, record.definition, record.schema),
                strict=True,
            ):
                declaration = bundle.get(
                    bytes.fromhex(REGISTRY_MAPS[role][key.hex()]), "declaration"
                )
                assert declaration in DECLARATIONS
    assert kinds == {"Object", "Relation", "Derivation"}


def test_codebook_replacement_never_redefines_concept_identity():
    bundle, _ = small()
    scope, snapshot = objects(bundle, "scope")[0], objects(bundle, "snapshot")[0]
    original = {p: identity(concept(scope, p)) for p in ("0", "1")}
    first = make_book(scope, snapshot, prefix_codes(Counter({"0": 100, "1": 1})))
    second = make_book(scope, snapshot, prefix_codes(Counter({"0": 1, "1": 100})))
    assert identity(first) != identity(second)
    assert read_book(first, bundle) != read_book(second, bundle)
    assert original == {p: identity(concept(scope, p)) for p in ("0", "1")}


def test_evidence_root_deduplication_and_conflicts():
    root, origin = digest(b"root"), digest(b"origin")
    repeated = tuple(Sample("0101" * 20, root, digest(str(i).encode())) for i in range(4))
    bundle, report = build("scope", repeated, engineering_samples("held", ["01"]))
    assert report["summary"]["training_observations"] == 1
    assert report["summary"]["candidate_concepts"] == 0
    with pytest.raises(ContractError, match="conflicting"):
        build(
            "scope",
            (Sample("0", root, origin), Sample("1", root, origin)),
            engineering_samples("held", ["1"]),
        )
    with pytest.raises(ContractError, match="leakage"):
        build("scope", repeated, repeated)
    assert verify_bundle(bundle) == report


def test_holdout_changes_do_not_change_fit_or_selection():
    first, first_report = small(test=["00000000"])
    second, second_report = small(test=["11101010"])
    for kind in ("snapshot", "concept", "evidence", "codebook", "predictor"):
        assert {identity(r) for r in objects(first, kind)} == {
            identity(r) for r in objects(second, kind)
        }
    assert first_report["summary"]["candidates"] == second_report["summary"]["candidates"]
    assert first_report["summary"]["selected"] == second_report["summary"]["selected"]


def test_scopes_do_not_share_concepts_or_accept_cross_scope_codebooks():
    first, _ = small("first")
    second, _ = small("second")
    assert not (
        {identity(r) for r in objects(first, "concept")}
        & {identity(r) for r in objects(second, "concept")}
    )
    expression = next(r for r in objects(first, "expression") if r.payload[64] == 1)
    other = objects(second, "codebook")[0]
    first.add(other)
    wrong = replace(
        expression, payload=expression.payload[:65] + identity(other) + expression.payload[97:]
    )
    with pytest.raises(ContractError, match="scope"):
        reconstruct(wrong, first)


def test_no_associations_across_observation_boundaries():
    bundle, report = small(train=["0", "1"], test=["01"])
    assert report["summary"]["association_edges"] == 0
    assert not [
        r
        for r in bundle.records.values()
        if isinstance(r, Relation) and r.relation_type == identity(LINKS["observed-follows"])
    ]


def test_pattern_discovery_requires_multiple_roots_and_never_uses_labels():
    samples = engineering_samples("independent", ["00001111", "00001111"])
    patterns, evidence = discover(samples, DEFAULT_CONFIG)
    assert patterns and all(set(p) <= {"0", "1"} for p in patterns)
    assert all(len(value["support_roots"]) == 2 for value in evidence.values())
    assert discover(samples[:1], DEFAULT_CONFIG)[0] == []


@pytest.mark.parametrize(
    "config",
    [
        dict(DEFAULT_CONFIG, max_pattern_bits=17),
        dict(DEFAULT_CONFIG, max_patterns=True),
        dict(DEFAULT_CONFIG, min_support=1),
        dict(DEFAULT_CONFIG, weights={"bits": 0, "encode": 0, "errors": 0, "decode": 0}),
    ],
)
def test_invalid_search_budgets(config):
    with pytest.raises(ContractError):
        build(
            "scope", engineering_samples("t", ["0"]), engineering_samples("h", ["1"]), config=config
        )


def test_input_and_collection_budgets():
    with pytest.raises(ContractError):
        build("scope", engineering_samples("t", ["0" * 4097]), engineering_samples("h", ["1"]))
    with pytest.raises(ContractError):
        build("scope", engineering_samples("t", ["0" * 4096] * 17), engineering_samples("h", ["1"]))
    with pytest.raises(ContractError):
        Bundle.read(b"bad")


def test_complete_replay_rejects_hash_valid_unexecuted_records():
    bundle, _ = small()
    scope = objects(bundle, "scope")[0]
    bundle.add(concept(scope, "0111111111111111"))
    with pytest.raises(ContractError, match="replay mismatch"):
        verify_bundle(bundle)


def test_artifact_corruption_and_no_overwrite(tmp_path):
    bundle, report = small()
    destination = tmp_path / "artifact"
    publish(destination, bundle, report)
    assert verify_directory(destination) == report
    with pytest.raises(ContractError, match="exists"):
        publish(destination, bundle, report)
    path = destination / "records.bin"
    damaged = bytearray(path.read_bytes())
    damaged[-1] ^= 1
    path.write_bytes(damaged)
    with pytest.raises(ContractError, match="digest"):
        verify_directory(destination)


def test_binary_collection_rejects_duplicate_or_unsorted_records():
    bundle, _ = small()
    data = bytearray(bundle.bytes())
    # Identity ordering is part of the frame contract, separate from each canonical record.
    first_id = data[13:45]
    first_length = int.from_bytes(data[45:49], "big")
    second_offset = 49 + first_length
    data[second_offset + 1 : second_offset + 33] = first_id
    with pytest.raises(ContractError, match="Duplicate or unsorted"):
        Bundle.read(bytes(data))


def test_active_adapter_is_read_only_and_preserves_received_root(tmp_path):
    path = tmp_path / "active.sqlite"
    store = Store.create(path, "adapter-test")
    for name, cp in (("a", 65), ("b", 66)):
        store.submit("atom", name=name, scalar=cp, max_steps=8, memory_limit=8)
    a, b = store.inspect("a")["id"], store.inspect("b")["id"]
    store.submit("group", name="ab", members=[a, b], max_steps=8, memory_limit=8)
    group = store.inspect("ab")["id"]
    event = store.submit("observe", instance=group, event="g", source="fixture", scalar=65)
    policy = store.output(store.submit("allow_forward", group=group, member=a), "policy")["id"]
    store.submit("observe", instance=a, event="local", source="fixture", scalar=66)
    store.submit("forward", policy=policy, receipt=event)
    root = store.output(event, "observation")["root"]
    before = store.snapshot()
    store.close()
    destination = tmp_path / "binary"
    report = from_active(path, "a", destination)
    assert report["summary"]["training_observations"] == 1
    assert report["summary"]["holdout_observations"] == 1
    bundle = Bundle.read((destination / "records.bin").read_bytes())
    assert root in {parse_observation(r)[2].root for r in objects(bundle, "observation")}
    reopened = Store.open(path)
    assert reopened.snapshot() == before
    assert reopened.inspect("b")["state"]["observations"] == 0
    reopened.close()


def test_independent_cli_replay(tmp_path):
    bundle, report = small()
    path = tmp_path / "published"
    publish(path, bundle, report)
    completed = subprocess.run(
        [sys.executable, "-m", "tools.binary_language", "verify", "--directory", str(path)],
        capture_output=True,
        text=True,
        check=True,
        timeout=20,
    )
    assert json.loads(completed.stdout) == report
    assert Bundle.read(bundle.bytes()).bytes() == bundle.bytes()


def test_unknown_encoding_and_source_corruption_rejected():
    bundle, _ = small()
    raw = next(r for r in objects(bundle, "expression") if r.payload[64] == 0)
    bad = replace(raw, payload=raw.payload[:64] + b"\x02" + raw.payload[65:])
    with pytest.raises(ContractError, match="Unsupported"):
        reconstruct(bad, bundle)
    wrong_binding = replace(raw, definition=b"x" * 32)
    with pytest.raises(ContractError, match="binding"):
        bundle.add(wrong_binding)
    assert encode(object_record("scope", b"fixture"))


def test_native_binary_path_has_no_unicode_or_provider_import_requirement():
    program = """
import sys
class NoProviderOrUnicode:
    def find_spec(self, fullname, path=None, target=None):
        if fullname in {'tools.active_objects', 'tools.unicode_objects', 'openai'}:
            raise RuntimeError('Unexpected input-format/provider dependency')
sys.meta_path.insert(0, NoProviderOrUnicode())
from tools.binary_language import build, engineering_samples
_, result = build('native', engineering_samples('train', ['0', '1']), engineering_samples('test', ['01']))
assert result['summary']['hard_constraints']['all_reconstructions_exact']
"""
    subprocess.run([sys.executable, "-c", program], check=True, timeout=20)


def test_encoding_work_weight_changes_the_selected_tradeoff():
    train = engineering_samples("weighted-train", ["00101101" * 256] * 12)
    test = engineering_samples("weighted-test", ["00101101" * 64])
    _, compact = build("weighted", train, test)
    config = dict(DEFAULT_CONFIG, weights={"bits": 1, "encode": 1000, "errors": 0, "decode": 0})
    _, cheap = build("weighted", train, test, config=config)
    assert compact["summary"]["selected"].startswith("prefix-")
    assert cheap["summary"]["selected"] == "raw"
    assert (
        cheap["summary"]["representation"]["training_selected_bits"]
        > compact["summary"]["representation"]["training_selected_bits"]
    )


def test_native_golden_and_independent_rebuild(tmp_path):
    golden = json.loads((ROOT / "fixtures/binary-language-v1/golden.json").read_text())["native"]
    first = demo(tmp_path / "first")
    second = demo(tmp_path / "second")
    assert first == second
    assert first["canonical_sha256"] == golden["canonical_sha256"]
    assert first["record_counts"] == golden["record_counts"]
    assert first["summary"]["selected"] == golden["selected"]
    assert first["summary"]["prediction"] == golden["prediction"]
    assert first["summary"]["representation"] == golden["representation"]
