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
"""M0.3: binary pattern concepts and lossless local codes over three immutable primitives."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from functools import cache
from pathlib import Path

from tools.binary_codec import (
    MAX_ENCODED_BITS,
    MAX_PATTERNS,
    Reader,
    bits_valid,
    decode_tokens,
    encode_tokens,
    pack_bits,
    prefix_codes,
    require,
    segment,
    validate_codes,
)
from tools.silicate_contract import (
    FORMAT,
    MAX_RECORD_BYTES,
    PRIMITIVE_KINDS,
    ContractError,
    Derivation,
    Object,
    Record,
    Reference,
    Relation,
    decode,
    encode,
    family,
    identity,
)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIRECTORY = ROOT / "data/experiments/binary-language/m0-3"
PROFILE = "sovereign-binary-language-v1"
MAGIC = b"SOVBIN1\n"
MAX_COLLECTION_BYTES = 16 * 1024 * 1024
KINDS = (
    "declaration",
    "registry",
    "scope",
    "source",
    "observation",
    "snapshot",
    "concept",
    "evidence",
    "codebook",
    "expression",
    "predictor",
    "prediction",
    "run",
    "report",
    "operation",
    "relation-type",
)
OPERATIONS = ("observe", "discover", "optimize", "associate", "predict", "validate")
RELATIONS = ("supported-by", "observed-follows", "belongs-to")
DEFAULT_CONFIG = {
    "max_pattern_bits": 16,
    "max_patterns": 16,
    "min_support": 2,
    "weights": {"bits": 1, "encode": 0, "errors": 0, "decode": 0},
}


def canonical(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode()


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def identifier(value: str) -> bytes:
    require(
        isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
        "Invalid canonical identity",
    )
    return bytes.fromhex(value)


@cache
def handle(role: str, kind: str) -> bytes:
    return hashlib.sha256(f"{PROFILE}:{role}:{kind}".encode()).digest()


def object_record(kind: str, payload: bytes) -> Object:
    require(kind in KINDS and isinstance(payload, bytes), "Invalid binary foundation Object")
    return Object(*(handle(role, kind) for role in ("type", "definition", "schema")), payload)


def json_object(kind: str, data) -> Object:
    return object_record(kind, canonical(data))


def kind_of(record: Record) -> str:
    require(isinstance(record, Object), "Expected an Object")
    for kind in KINDS:
        if record.object_type == handle("type", kind):
            require(
                record.definition == handle("definition", kind)
                and record.schema == handle("schema", kind),
                "Invalid declaration binding",
            )
            return kind
    raise ContractError("Unknown binary foundation Object type")


def declarations() -> tuple[dict, tuple[Object, ...]]:
    records, maps = [], {role: {} for role in ("type", "definition", "schema")}
    for kind in KINDS:
        for role in maps:
            declaration = json_object(
                "declaration",
                {
                    "profile": PROFILE,
                    "kind": kind,
                    "role": role,
                    "handle": handle(role, kind).hex(),
                    "contract": "BINARY_FOUNDATION.md:v1",
                    "domain_validator": "binary_language.py:v1",
                    "semantics": "engineering-contract; no English lexical meaning",
                },
            )
            records.append(declaration)
            maps[role][handle(role, kind).hex()] = identity(declaration).hex()
    return maps, tuple(records)


REGISTRY_MAPS, DECLARATIONS = declarations()
REGISTRY = json_object("registry", {"profile": PROFILE, "maps": REGISTRY_MAPS})
OPS = {
    name: json_object("operation", {"name": name, "version": 1, "profile": PROFILE})
    for name in OPERATIONS
}
LINKS = {
    name: json_object("relation-type", {"name": name, "profile": PROFILE}) for name in RELATIONS
}


class Bundle:
    """A physical immutable collection, not an additional semantic primitive."""

    def __init__(self):
        self.records: dict[bytes, Record] = {}

    def add(self, record: Record) -> Object | Relation | Derivation:
        wire = encode(record)
        rid = identity(record)
        require(rid not in self.records or encode(self.records[rid]) == wire, "Identity collision")
        if isinstance(record, Object):
            kind_of(record)
        self.records[rid] = record
        return record

    def get(self, rid: bytes, kind: str | None = None) -> Record:
        require(rid in self.records, "Unresolved record reference")
        record = self.records[rid]
        if kind is not None:
            require(kind_of(record) == kind, "Unexpected referenced Object type")
        return record

    def relation(self, source: Object, name: str, target: Object, context: bytes = b"") -> Relation:
        return self.add(
            Relation(identity(source), identity(LINKS[name]), identity(target), None, context)
        )

    def receipt(self, operation: str, inputs: list[Record], outputs: list[Record], parameters=None):
        return self.add(
            Derivation(
                "deterministic",
                tuple(Reference(family(r), identity(r)) for r in inputs),
                identity(OPS[operation]),
                identity(OPS[operation]),
                1,
                canonical({"profile": PROFILE, "parameters": parameters}),
                tuple(Reference(family(r), identity(r)) for r in outputs),
            )
        )

    def bytes(self) -> bytes:
        require(len(self.records) <= 8192, "Record-count budget exceeded")
        frames = [MAGIC, len(self.records).to_bytes(4, "big")]
        for rid, record in sorted(self.records.items()):
            wire = encode(record)
            frames.extend(
                (
                    bytes([PRIMITIVE_KINDS.index(family(record))]),
                    rid,
                    len(wire).to_bytes(4, "big"),
                    wire,
                )
            )
        result = b"".join(frames)
        require(len(result) <= MAX_COLLECTION_BYTES, "Collection byte budget exceeded")
        return result

    def validate(self) -> None:
        for declaration in (*DECLARATIONS, REGISTRY, *OPS.values(), *LINKS.values()):
            require(
                self.get(identity(declaration)) == declaration, "Bootstrap declaration mismatch"
            )
        for rid, record in self.records.items():
            require(decode(family(record), encode(record), rid) == record, "Record mismatch")
            if isinstance(record, Object):
                kind_of(record)
                for role, key in zip(
                    ("type", "definition", "schema"),
                    (record.object_type, record.definition, record.schema),
                    strict=True,
                ):
                    self.get(identifier(REGISTRY_MAPS[role][key.hex()]), "declaration")
            elif isinstance(record, Relation):
                require(
                    isinstance(self.get(record.source), Object)
                    and isinstance(self.get(record.target), Object),
                    "Non-Object relation endpoint",
                )
                self.get(record.relation_type, "relation-type")
            else:
                self.get(record.operation, "operation")
                self.get(record.rule, "operation")
                require(
                    record.execution_class == "deterministic" and record.rule_version == 1,
                    "Unsupported derivation contract",
                )
                for reference in (*record.inputs, *record.outputs):
                    require(
                        family(self.get(reference.identity)) == reference.kind,
                        "Reference family mismatch",
                    )

    @classmethod
    def read(cls, data: bytes) -> Bundle:
        require(len(data) <= MAX_COLLECTION_BYTES, "Collection byte budget exceeded")
        reader = Reader(data)
        require(reader.take(len(MAGIC)) == MAGIC, "Invalid binary collection header")
        count = reader.uint(4)
        require(count <= 8192, "Record-count budget exceeded")
        bundle, previous = cls(), None
        for _ in range(count):
            tag, rid, size = reader.uint(1), reader.take(32), reader.uint(4)
            require(tag < 3 and size <= MAX_RECORD_BYTES, "Invalid framed record")
            require(previous is None or previous < rid, "Duplicate or unsorted record identity")
            bundle.add(decode(PRIMITIVE_KINDS[tag], reader.take(size), rid))
            previous = rid
        reader.finish()
        bundle.validate()
        return bundle


@dataclass(frozen=True)
class Sample:
    """Input helper; its persistent form is an observation Object."""

    bits: str
    root: str
    origin: str


def check_config(config: dict) -> None:
    require(
        isinstance(config, dict) and set(config) == set(DEFAULT_CONFIG), "Invalid configuration"
    )
    for key, low, high in (
        ("max_pattern_bits", 2, 16),
        ("max_patterns", 0, MAX_PATTERNS),
        ("min_support", 2, 128),
    ):
        require(type(config[key]) is int and low <= config[key] <= high, "Invalid search budget")
    weights = config["weights"]
    require(
        isinstance(weights, dict)
        and set(weights) == set(DEFAULT_CONFIG["weights"])
        and all(type(value) is int and 0 <= value <= 1000 for value in weights.values())
        and weights["bits"] > 0,
        "Invalid objective weights",
    )


def unique_samples(samples: tuple[Sample, ...]) -> tuple[Sample, ...]:
    require(
        isinstance(samples, tuple) and 1 <= len(samples) <= 128, "Observation-count budget exceeded"
    )
    roots = {}
    for sample in samples:
        require(isinstance(sample, Sample), "Invalid observation input")
        bits_valid(sample.bits)
        identifier(sample.root)
        identifier(sample.origin)
        require(
            sample.root not in roots or roots[sample.root].bits == sample.bits,
            "Same evidence root has conflicting content",
        )
        roots.setdefault(sample.root, sample)
    return tuple(roots.values())


def parse_observation(record: Object) -> tuple[bytes, bytes, Sample, int]:
    require(kind_of(record) == "observation", "Expected binary observation")
    reader = Reader(record.payload)
    scope, source, root, origin, split = (
        reader.take(32),
        reader.take(32),
        reader.take(32),
        reader.take(32),
        reader.uint(1),
    )
    require(split in (0, 1), "Invalid observation split")
    bits = reader.bits()
    reader.finish()
    return scope, source, Sample(bits, root.hex(), origin.hex()), split


def concept(scope: Object, pattern: str) -> Object:
    return object_record("concept", identity(scope) + pack_bits(pattern, 16))


def discover(samples: tuple[Sample, ...], config: dict) -> tuple[list[str], dict]:
    counts, support = Counter(), defaultdict(set)
    for sample in samples:
        for size in range(2, config["max_pattern_bits"] + 1):
            for offset in range(max(0, len(sample.bits) - size + 1)):
                pattern = sample.bits[offset : offset + size]
                counts[pattern] += 1
                support[pattern].add(sample.root)
    candidates = [p for p in counts if len(support[p]) >= config["min_support"]]
    candidates.sort(key=lambda p: (-(len(p) - 1) * counts[p], -len(support[p]), -len(p), p))
    chosen = candidates[: config["max_patterns"]]
    evidence = {
        p: {"occurrences_including_overlaps": counts[p], "support_roots": sorted(support[p])}
        for p in chosen
    }
    return chosen, evidence


def make_book(scope: Object, snapshot: Object, codes: dict[str, str]) -> Object:
    validate_codes(codes)
    chunks = [identity(scope), identity(snapshot), len(codes).to_bytes(2, "big")]
    for pattern, code in sorted(codes.items()):
        chunks.extend(
            (identity(concept(scope, pattern)), pack_bits(pattern, 16), pack_bits(code, 64))
        )
    return object_record("codebook", b"".join(chunks))


def read_book(book: Object, bundle: Bundle) -> dict[str, str]:
    require(kind_of(book) == "codebook", "Expected codebook")
    reader = Reader(book.payload)
    scope = bundle.get(reader.take(32), "scope")
    snapshot = bundle.get(reader.take(32), "snapshot")
    require(snapshot.payload[:32] == identity(scope), "Codebook snapshot scope mismatch")
    count = reader.uint(2)
    require(2 <= count <= MAX_PATTERNS + 2, "Codebook budget exceeded")
    codes = {}
    previous = None
    for _ in range(count):
        rid, pattern, code = reader.take(32), reader.bits(16), reader.bits(64)
        require(previous is None or previous < pattern, "Duplicate or unsorted codebook pattern")
        require(
            bundle.get(rid, "concept") == concept(scope, pattern),
            "Concept identity changed by codebook",
        )
        codes[pattern], previous = code, pattern
    reader.finish()
    validate_codes(codes)
    return codes


def expression(
    scope: Object, observation: Object, bits: str, book: Object | None, codes: dict[str, str] | None
) -> tuple[Object, int, int, tuple[str, ...]]:
    base = identity(scope) + identity(observation)
    if book is None:
        return (
            object_record("expression", base + b"\x00" + pack_bits(bits)),
            len(bits),
            len(bits),
            tuple(bits),
        )
    tokens, work = segment(bits, tuple(codes))
    encoded = encode_tokens(tokens, codes)
    value = object_record(
        "expression",
        base
        + b"\x01"
        + identity(book)
        + len(bits).to_bytes(4, "big")
        + len(tokens).to_bytes(4, "big")
        + pack_bits(encoded, MAX_ENCODED_BITS),
    )
    return value, work + len(encoded), len(encoded), tokens


def reconstruct(record: Object, bundle: Bundle) -> str:
    require(kind_of(record) == "expression", "Expected expression")
    reader = Reader(record.payload)
    scope = bundle.get(reader.take(32), "scope")
    observation = bundle.get(reader.take(32), "observation")
    require(
        parse_observation(observation)[0] == identity(scope),
        "Expression observation scope mismatch",
    )
    mode = reader.uint(1)
    require(mode in (0, 1), "Unsupported expression encoding")
    if mode == 0:
        bits = reader.bits()
    else:
        book = bundle.get(reader.take(32), "codebook")
        require(book.payload[:32] == identity(scope), "Expression codebook scope mismatch")
        codes = read_book(book, bundle)
        length, count = reader.uint(4), reader.uint(4)
        bits, _ = decode_tokens(reader.bits(MAX_ENCODED_BITS), codes, length, count)
    reader.finish()
    require(bits == parse_observation(observation)[2].bits, "Lossless reconstruction failed")
    return bits


def fit_predictor(samples: tuple[Sample, ...], patterns: tuple[str, ...]) -> dict:
    counts, global_counts = defaultdict(Counter), Counter()
    for sample in samples:
        for i in range(1, len(sample.bits)):
            bit = sample.bits[i]
            global_counts[bit] += 1
            for pattern in patterns:
                if i >= len(pattern) and sample.bits[i - len(pattern) : i] == pattern:
                    counts[pattern][bit] += 1
    return {
        "global": [global_counts["0"], global_counts["1"]],
        "contexts": {p: [counts[p]["0"], counts[p]["1"]] for p in sorted(patterns)},
    }


def predict(bits: str, model: dict) -> tuple[str, int, int]:
    majority = "1" if model["global"][1] > model["global"][0] else "0"
    predictions = []
    choices = sorted(model["contexts"], key=lambda p: (-len(p), p))
    for i in range(1, len(bits)):
        value = majority
        for pattern in choices:
            counts = model["contexts"][pattern]
            if sum(counts) and i >= len(pattern) and bits[i - len(pattern) : i] == pattern:
                value = "1" if counts[1] > counts[0] else "0"
                break
        predictions.append(value)
    errors = sum(a != b for a, b in zip(predictions, bits[1:], strict=True))
    baseline = sum(majority != bit for bit in bits[1:])
    return "".join(predictions), errors, baseline


def storage_bits(records: list[Record]) -> int:
    unique = {identity(record): record for record in records}
    return 8 * (len(MAGIC) + 4 + sum(37 + len(encode(record)) for record in unique.values()))


def predictor_record(scope: Object, snapshot: Object, model: dict) -> Object:
    parts = [
        identity(scope),
        identity(snapshot),
        *(n.to_bytes(4, "big") for n in model["global"]),
        len(model["contexts"]).to_bytes(2, "big"),
    ]
    for pattern, counts in sorted(model["contexts"].items()):
        parts.extend((identity(concept(scope, pattern)), *(n.to_bytes(4, "big") for n in counts)))
    return object_record("predictor", b"".join(parts))


def build(
    scope_name: str,
    training: tuple[Sample, ...],
    holdout: tuple[Sample, ...],
    source: dict | None = None,
    config: dict | None = None,
) -> tuple[Bundle, dict]:
    """Train/choose on training only; freeze that result before observing held-out outcomes."""
    config = json.loads(canonical(DEFAULT_CONFIG if config is None else config))
    check_config(config)
    require(
        isinstance(scope_name, str) and 1 <= len(scope_name.encode()) <= 512, "Invalid scope label"
    )
    training, holdout = unique_samples(training), unique_samples(holdout)
    require(
        not ({s.root for s in training} & {s.root for s in holdout}),
        "Training/holdout root leakage",
    )
    require(sum(len(s.bits) for s in (*training, *holdout)) <= 65536, "Total bit budget exceeded")
    source = source or {"kind": "raw-bits", "reference": "explicit-local-observations"}
    require(
        isinstance(source, dict)
        and set(source) == {"kind", "reference"}
        and source["kind"] in {"raw-bits", "engineering", "active-objects"}
        and isinstance(source["reference"], str)
        and len(source["reference"]) <= 8192,
        "Invalid observation source descriptor",
    )
    bundle = Bundle()
    for record in (*DECLARATIONS, REGISTRY, *OPS.values(), *LINKS.values()):
        bundle.add(record)
    scope = bundle.add(object_record("scope", scope_name.encode()))
    source_record = bundle.add(json_object("source", source))
    observations = []
    for split, samples in enumerate((training, holdout)):
        group = []
        for sample in samples:
            group.append(
                bundle.add(
                    object_record(
                        "observation",
                        identity(scope)
                        + identity(source_record)
                        + identifier(sample.root)
                        + identifier(sample.origin)
                        + bytes([split])
                        + pack_bits(sample.bits),
                    )
                )
            )
        observations.append(group)
    train_records, test_records = observations
    bundle.receipt(
        "observe",
        [scope, source_record],
        train_records + test_records,
        {"input_kind": source["kind"], "scope_isolated": True},
    )
    snapshot = bundle.add(
        object_record(
            "snapshot",
            identity(scope)
            + len(training).to_bytes(2, "big")
            + b"".join(identity(r) for r in train_records),
        )
    )
    run = bundle.add(
        json_object(
            "run",
            {
                "profile": PROFILE,
                "scope": identity(scope).hex(),
                "source": identity(source_record).hex(),
                "training": [identity(r).hex() for r in train_records],
                "holdout": [identity(r).hex() for r in test_records],
                "config": config,
                "learner_ingestion_allowed": False,
            },
        )
    )
    ranked, evidence = discover(training, config)
    concepts, discovery_outputs = {}, []
    for pattern in ("0", "1", *ranked):
        value = bundle.add(concept(scope, pattern))
        concepts[pattern] = value
        discovery_outputs.extend((value, bundle.relation(value, "belongs-to", scope)))
        if pattern in evidence:
            claim = bundle.add(
                json_object(
                    "evidence",
                    {
                        "concept": identity(value).hex(),
                        "training_snapshot": identity(snapshot).hex(),
                        "status": "candidate-pattern",
                        **evidence[pattern],
                        "meaning": "exact scoped bit-pattern occurrence; no lexical or causal claim",
                    },
                )
            )
            discovery_outputs.extend((claim, bundle.relation(value, "supported-by", claim)))
    bundle.receipt(
        "discover",
        [scope, snapshot, *train_records],
        discovery_outputs,
        {k: config[k] for k in ("max_pattern_bits", "max_patterns", "min_support")},
    )

    # Finite hypothesis search. Raw storage is always a candidate and ties favor it.
    sizes = sorted({0, min(4, len(ranked)), min(8, len(ranked)), len(ranked)})
    plans, optimization_outputs = [], []
    for size in [None, *sizes]:
        name = "raw" if size is None else f"prefix-{size}"
        patterns = ("0", "1", *ranked[:size]) if size is not None else ("0", "1")
        codes, book = None, None
        if size is not None:
            counts = Counter({p: 0 for p in patterns})
            for sample in training:
                counts.update(segment(sample.bits, patterns)[0])
            codes = prefix_codes(counts)
            book = bundle.add(make_book(scope, snapshot, codes))
            optimization_outputs.append(book)
        outputs, encode_work, decode_work, token_sequences = [], 0, 0, []
        for sample, observation in zip(training, train_records, strict=True):
            value, work, decoding, tokens = expression(scope, observation, sample.bits, book, codes)
            bundle.add(value)
            require(reconstruct(value, bundle) == sample.bits, "Candidate is not lossless")
            outputs.append(value)
            encode_work += work
            decode_work += decoding
            token_sequences.append(tokens)
        model = fit_predictor(training, patterns)
        model_record = bundle.add(predictor_record(scope, snapshot, model))
        train_errors = sum(predict(sample.bits, model)[1] for sample in training)
        fit_checks = sum(max(0, len(s.bits) - 1) for s in training) * len(patterns)
        encoding_package = ([book, *(concepts[p] for p in patterns)] if book else []) + outputs
        measurements = {
            "bits": storage_bits(encoding_package),
            "encode": encode_work + fit_checks,
            "errors": train_errors,
            "decode": decode_work + (len(codes) if codes else 0),
        }
        score = sum(config["weights"][key] * value for key, value in measurements.items())
        metrics = {
            "name": name,
            "measurements": measurements,
            "weighted_score": score,
            "book": identity(book).hex() if book else None,
            "predictor": identity(model_record).hex(),
            "training_only": True,
            "lossless": True,
        }
        metric_record = bundle.add(json_object("report", {"candidate": metrics}))
        optimization_outputs.extend([*outputs, model_record, metric_record])
        plans.append(
            {
                "metrics": metrics,
                "patterns": patterns,
                "codes": codes,
                "book": book,
                "model": model,
                "model_record": model_record,
                "expressions": outputs,
                "token_sequences": token_sequences,
            }
        )
    winner = min(
        enumerate(plans), key=lambda item: (item[1]["metrics"]["weighted_score"], item[0])
    )[1]
    bundle.receipt(
        "optimize",
        [snapshot, *train_records, *concepts.values()],
        optimization_outputs,
        {"weights": config["weights"], "selection_data": "training-only"},
    )

    transitions = Counter()
    for tokens in winner["token_sequences"]:
        transitions.update(
            zip(tokens, tokens[1:], strict=False)
        )  # No links across event boundaries.
    associations = []
    for (left, right), count in sorted(transitions.items()):
        associations.append(
            bundle.relation(
                concepts[left],
                "observed-follows",
                concepts[right],
                identity(snapshot) + count.to_bytes(4, "big"),
            )
        )
    bundle.receipt(
        "associate",
        [snapshot, *winner["expressions"]],
        associations,
        {"claim": "within-observation association; not causation"},
    )

    test_expressions, predictions = [], []
    test_errors, baseline_errors, target_bits = 0, 0, 0
    for sample, observation in zip(holdout, test_records, strict=True):
        value, _, _, _ = expression(
            scope, observation, sample.bits, winner["book"], winner["codes"]
        )
        bundle.add(value)
        require(reconstruct(value, bundle) == sample.bits, "Holdout reconstruction failed")
        test_expressions.append(value)
        predicted, errors, baseline = predict(sample.bits, winner["model"])
        predictions.append(
            bundle.add(
                object_record(
                    "prediction",
                    identity(observation) + identity(winner["model_record"]) + pack_bits(predicted),
                )
            )
        )
        test_errors += errors
        baseline_errors += baseline
        target_bits += len(predicted)
    bundle.receipt(
        "predict",
        [winner["model_record"], *test_records],
        predictions,
        {"evaluation": "one-step-next-bit, observed-prefix context, frozen training model"},
    )
    selected_package = (
        [winner["book"], *(concepts[p] for p in winner["patterns"])] if winner["book"] else []
    )
    raw_holdout = [
        expression(scope, record, sample.bits, None, None)[0]
        for sample, record in zip(holdout, test_records, strict=True)
    ]
    summary = {
        "scope": identity(scope).hex(),
        "profile": PROFILE,
        "selected": winner["metrics"]["name"],
        "training_observations": len(training),
        "holdout_observations": len(holdout),
        "candidate_concepts": len(ranked),
        "literal_fallbacks": 2,
        "association_edges": len(associations),
        "concept_status": "observational-pattern-candidates",
        "candidates": [plan["metrics"] for plan in plans],
        "weights": config["weights"],
        "representation": {
            "training_selected_bits": winner["metrics"]["measurements"]["bits"],
            "training_raw_bits": plans[0]["metrics"]["measurements"]["bits"],
            "holdout_selected_standalone_bits": storage_bits(selected_package + test_expressions),
            "holdout_raw_bits": storage_bits(raw_holdout),
            "counting": "canonical concept/codebook/expression bytes, IDs, framing and padding; audit archive separate",
        },
        "prediction": {
            "targets": target_bits,
            "errors": test_errors,
            "majority_baseline_errors": baseline_errors,
            "improved_over_majority": target_bits > 0 and test_errors < baseline_errors,
            "semantic_error": None,
        },
        "hard_constraints": {
            "all_reconstructions_exact": True,
            "train_holdout_roots_disjoint": True,
            "scope_isolated": True,
            "concept_ids_immutable": True,
        },
        "learner_ingestion_allowed": False,
        "semantic_understanding": "not_established",
        "subjective_experience": "not_established",
    }
    report_record = bundle.add(json_object("report", {"evaluation": summary}))
    bundle.receipt(
        "validate",
        [
            run,
            winner["model_record"],
            *test_records,
            *predictions,
            *test_expressions,
            *winner["expressions"],
        ],
        [report_record, *test_expressions],
        {"exact_reconstruction_required": True},
    )
    bundle.validate()
    packed = bundle.bytes()
    return bundle, {
        "run_id": identity(run).hex(),
        "report_id": identity(report_record).hex(),
        "summary": summary,
        "record_counts": dict(Counter(family(r) for r in bundle.records.values())),
        "canonical_sha256": digest(packed),
        "audit_archive_bytes": len(packed),
    }


def verify_bundle(bundle: Bundle) -> dict:
    bundle.validate()
    runs = [r for r in bundle.records.values() if isinstance(r, Object) and kind_of(r) == "run"]
    require(len(runs) == 1, "Collection requires exactly one run")
    run = json.loads(runs[0].payload)
    require(
        set(run)
        == {
            "profile",
            "scope",
            "source",
            "training",
            "holdout",
            "config",
            "learner_ingestion_allowed",
        }
        and run["profile"] == PROFILE
        and run["learner_ingestion_allowed"] is False,
        "Invalid engineering run contract",
    )
    scope, source = (
        bundle.get(identifier(run["scope"]), "scope"),
        bundle.get(identifier(run["source"]), "source"),
    )
    groups = []
    for split, key in enumerate(("training", "holdout")):
        samples = []
        for rid in run[key]:
            sid, src, sample, role = parse_observation(bundle.get(identifier(rid), "observation"))
            require(
                sid == identity(scope) and src == identity(source) and role == split,
                "Observation scope/source/split mismatch",
            )
            samples.append(sample)
        groups.append(tuple(samples))
    rebuilt, report = build(
        scope.payload.decode(), *groups, json.loads(source.payload), run["config"]
    )
    require(bundle.bytes() == rebuilt.bytes(), "Deterministic foundation replay mismatch")
    return report


def publish(directory: Path, bundle: Bundle, report: dict) -> dict:
    require(not directory.exists(), "Destination exists; use a new immutable snapshot directory")
    require(verify_bundle(bundle) == report, "Report mismatch before publishing")
    directory.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".binary-staging-", dir=directory.parent) as temporary:
        staging = Path(temporary) / "artifact"
        staging.mkdir()
        (staging / "records.bin").write_bytes(bundle.bytes())
        (staging / "report.json").write_text(json.dumps(report, indent=2) + "\n")
        manifest = {
            "profile": PROFILE,
            "format": FORMAT,
            "learner_ingestion_allowed": False,
            "implementation_sha256": {
                name: digest((ROOT / name).read_bytes())
                for name in ("tools/binary_codec.py", "tools/binary_language.py")
            },
            "file_sha256": {
                name: digest((staging / name).read_bytes())
                for name in ("records.bin", "report.json")
            },
        }
        (staging / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        verify_directory(staging)
        require(not directory.exists(), "Destination appeared during publishing")
        os.rename(staging, directory)
    return report


def verify_directory(directory: Path) -> dict:
    manifest = json.loads((directory / "manifest.json").read_text())
    require(
        manifest["profile"] == PROFILE
        and manifest["format"] == FORMAT
        and manifest["learner_ingestion_allowed"] is False,
        "Invalid artifact manifest",
    )
    require(
        set(manifest["file_sha256"]) == {"records.bin", "report.json"}, "Unexpected artifact files"
    )
    for name, expected in manifest["file_sha256"].items():
        require(
            (directory / name).stat().st_size <= MAX_COLLECTION_BYTES,
            "Artifact size exceeds budget",
        )
        require(digest((directory / name).read_bytes()) == expected, "Artifact digest mismatch")
    bundle = Bundle.read((directory / "records.bin").read_bytes())
    replayed = verify_bundle(bundle)
    require(
        replayed == json.loads((directory / "report.json").read_text()), "Saved report mismatch"
    )
    return replayed


def engineering_samples(label: str, values: list[str]) -> tuple[Sample, ...]:
    return tuple(
        Sample(bits, digest(f"{label}:root:{i}".encode()), digest(f"{label}:event:{i}".encode()))
        for i, bits in enumerate(values)
    )


def demo(directory: Path) -> dict:
    motif = "00101101"
    train = [(motif * 257)[i : i + 2048] for i in range(12)]
    test = [(motif * 258)[i : i + 2051] for i in range(12, 16)]
    bundle, report = build(
        "binary-engineering-environment-v1",
        engineering_samples("train", train),
        engineering_samples("holdout", test),
        {"kind": "engineering", "reference": "deterministic-periodic-bit-environment-v1"},
    )
    return publish(directory, bundle, report)


def from_active(path: Path, name: str, directory: Path) -> dict:
    from tools.active_objects import Store, unpack

    store = Store.open(path)
    try:
        view = store.inspect(name)
        samples = []
        for rid in view["state"]["memory"]:
            observation = unpack(store.get(identifier(rid)), "observation")[1]
            require(observation["instance"] == view["id"], "Active adapter crossed instance scope")
            symbol = store.get(identifier(observation["symbol"]))
            bits = "".join(f"{byte:08b}" for byte in symbol.payload)
            samples.append(Sample(bits, observation["root"], rid))
        samples = unique_samples(tuple(samples))
        require(
            len(samples) >= 2, "Adapter requires at least two distinct evidence roots for holdout"
        )
        source = {
            "kind": "active-objects",
            "reference": canonical(
                {
                    "instance": view["id"],
                    "state": view["state_id"],
                    "snapshot": store.snapshot()["canonical_sha256"],
                    "feature": "unicode-scalar-u32-big-endian",
                }
            ).decode(),
        }
    finally:
        store.close()
    bundle, report = build("active-instance:" + view["id"], samples[:-1], samples[-1:], source)
    return publish(directory, bundle, report)


def from_json(path: Path, directory: Path) -> dict:
    require(path.stat().st_size <= 1024 * 1024, "Input JSON exceeds budget")
    data = json.loads(path.read_text())
    require(
        set(data) == {"scope", "training", "holdout", "source", "config"}, "Invalid input fields"
    )
    groups = []
    for key in ("training", "holdout"):
        require(isinstance(data[key], list), "Expected observation list")
        for sample in data[key]:
            require(
                isinstance(sample, dict) and set(sample) == {"bits", "root", "origin"},
                "Invalid sample fields",
            )
        groups.append(tuple(Sample(**sample) for sample in data[key]))
    bundle, report = build(data["scope"], *groups, data["source"], data["config"])
    return publish(directory, bundle, report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("demo", "build", "from-active", "verify", "inspect"))
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY / "native")
    parser.add_argument("--input", type=Path)
    parser.add_argument(
        "--active-store",
        type=Path,
        default=ROOT / "data/experiments/active-objects/m0-2/records.sqlite",
    )
    parser.add_argument("--instance", default="atom-a")
    parser.add_argument("--id", help="Optional exact record identity for inspect")
    args = parser.parse_args()
    try:
        if args.command == "demo":
            result = demo(args.directory)
        elif args.command == "build":
            require(args.input is not None, "build requires --input")
            result = from_json(args.input, args.directory)
        elif args.command == "from-active":
            result = from_active(args.active_store, args.instance, args.directory)
        else:
            result = verify_directory(args.directory)
            if args.command == "inspect" and args.id:
                bundle = Bundle.read((args.directory / "records.bin").read_bytes())
                record = bundle.get(identifier(args.id))
                result = {
                    "id": args.id,
                    "primitive": family(record),
                    "canonical_hex": encode(record).hex(),
                }
                if isinstance(record, Object):
                    result.update(
                        {
                            "type": kind_of(record),
                            "payload_hex": record.payload.hex(),
                            "declarations": {
                                role: REGISTRY_MAPS[role][key.hex()]
                                for role, key in zip(
                                    ("type", "definition", "schema"),
                                    (record.object_type, record.definition, record.schema),
                                    strict=True,
                                )
                            },
                        }
                    )
        print(json.dumps(result, indent=2))
        return 0
    except (ContractError, OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Binary foundation operation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
