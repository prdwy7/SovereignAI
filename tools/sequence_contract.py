"""Sequence engineering envelope, not learner knowledge or a mastery assessment.

Structural validation only: source/span/sequence and domain semantics require
FULL REPLAY in the next module. No vocabulary, subject facts, or evaluation
answers are supplied here. Only Object, Relation, and Derivation persist.
"""

from __future__ import annotations

import hashlib
import json

from tools import unicode_objects
from tools.silicate_contract import (
    FORMAT,
    MAX_RECORD_BYTES,
    ContractError,
    Derivation,
    Object,
    Record,
    Relation,
    decode,
    encode,
    family,
    identity,
)

PROFILE = "sovereign-unicode-sequence-v1"
MAX_SOURCE_BYTES = 4096
MAX_SCALARS = 1024
MAX_RECORDS = 4096
MAX_PACK_BYTES = 2 * 1024 * 1024
MAGIC = b"SOVSEQ1\n"
KINDS = (
    "declaration",
    "source-bytes",
    "sequence",
    "span-map",
    "result",
    "operation",
    "rule",
    "relation-type",
)
_ROLES = ("type", "definition", "schema")
_FAMILIES = ("object", "relation", "derivation")


def require(condition, message):
    if not condition:
        raise ContractError(message)


def canonical(value) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, OverflowError, RecursionError) as exc:
        raise ContractError("Value is not canonical JSON") from exc


def handle(role, kind) -> bytes:
    require(role in _ROLES and kind in KINDS, "Unknown local declaration handle")
    return hashlib.sha256(f"{PROFILE}:{role}:{kind}".encode("ascii")).digest()


def obj(kind, payload: bytes) -> Object:
    require(kind in KINDS, "Unknown local object kind")
    require(isinstance(payload, bytes), "Payload must be bytes")
    record = Object(*(handle(role, kind) for role in _ROLES), payload)
    encode(record)
    return record


def jobj(kind, value) -> Object:
    return obj(kind, canonical(value))


_SPECS = {
    "declaration": {
        "encoding": "canonical-json",
        "fields": ["role", "name", "handle", "spec"],
        "meaning": "finite engineering type, definition, or schema declaration",
    },
    "source-bytes": {
        "encoding": "bytes",
        "maximum_bytes": MAX_SOURCE_BYTES,
        "meaning": "exact source bytes; interpretation checked by full replay",
    },
    "sequence": {
        "encoding": "u64-big-endian-count followed by ordered 32-byte child IDs",
        "maximum_count": MAX_SCALARS,
        "children": "Unicode scalar Object identities",
        "meaning": "ordered scalar sequence; full replay checks children and source",
    },
    "span-map": {
        "encoding": "canonical-json",
        "meaning": "mapping between source byte intervals and scalar positions",
        "offsets": "half-open byte offsets [start,end)",
        "positions": "zero-based scalar positions in the referenced sequence",
        "references": "source Object ID and sequence Object ID",
        "validation": "full replay checks mapping shape, coverage and bounds",
    },
    "result": {
        "encoding": "canonical-json",
        "statuses": ["accepted", "rejected"],
        "meaning": "sequence processing outcome; full replay verifies outcome",
    },
    "operation": {
        "encoding": "canonical-json",
        "meaning": "engineering operation descriptor, not an executable primitive",
    },
    "rule": {
        "encoding": "canonical-json",
        "meaning": "engineering replay rule descriptor",
    },
    "relation-type": {
        "encoding": "canonical-json",
        "meaning": "engineering relation type descriptor",
    },
}


def _bootstrap():
    registry = {
        "profile": PROFILE,
        "format": FORMAT,
        "maps": {role: dict(unicode_objects.EXPECTED_REGISTRY["maps"][role]) for role in _ROLES},
    }
    declarations = []
    for kind in KINDS:
        for role in _ROLES:
            spec = dict(_SPECS[kind])
            spec["declaration_role"] = role
            spec["profile"] = PROFILE
            record = jobj(
                "declaration",
                {
                    "role": role,
                    "name": kind,
                    "handle": handle(role, kind).hex(),
                    "spec": spec,
                },
            )
            key = handle(role, kind).hex()
            require(key not in registry["maps"][role], "Declaration handle collision")
            registry["maps"][role][key] = identity(record).hex()
            declarations.append(record)
    return registry, tuple(declarations)


REGISTRY, _LOCAL_DECLARATIONS = _bootstrap()
DECLARATIONS = _LOCAL_DECLARATIONS + tuple(unicode_objects.DECLARATION_RECORDS)
_FIXED_REGISTRY = canonical(REGISTRY)
_DECLARATION_BY_ID = {identity(record): record for record in DECLARATIONS}
_BINDINGS = {tuple(handle(role, kind) for role in _ROLES): kind for kind in KINDS}
_BINDINGS.update(
    {
        tuple(unicode_objects.handle(role, name) for role in _ROLES): label
        for name, label in (
            ("unicode-scalar", "unicode-scalar"),
            ("declaration", "unicode-declaration"),
        )
    }
)


def kind_of(record) -> str:
    if isinstance(record, Object):
        binding = (record.object_type, record.definition, record.schema)
        try:
            return _BINDINGS[binding]
        except (KeyError, TypeError):
            raise ContractError("Unknown or mixed Object binding") from None
    return family(record)


def _canonical_payload(payload):
    def reject_constant(value):
        raise ContractError("Nonfinite JSON constant")

    try:
        value = json.loads(payload.decode("ascii"), parse_constant=reject_constant)
        require(canonical(value) == payload, "Noncanonical JSON payload")
    except (UnicodeError, ValueError, TypeError, RecursionError) as exc:
        raise ContractError("Invalid canonical JSON payload") from exc


class Bundle:
    """Bounded canonical frame collection; validate() is not full replay."""

    def __init__(self):
        self.records: dict[bytes, Record] = {}

    def add(self, record) -> bytes:
        wire = encode(record)
        key = identity(record)
        require(decode(family(record), wire, key) == record, "Noncanonical record")
        if key in self.records:
            require(self.records[key] == record, "Conflicting existing identity")
        else:
            require(len(self.records) < MAX_RECORDS, "Excessive record count")
            self.records[key] = record
        return key

    def pack(self) -> bytes:
        require(len(self.records) <= MAX_RECORDS, "Excessive record count")
        out = bytearray(MAGIC)
        out.extend(len(self.records).to_bytes(4, "big"))
        for key in sorted(self.records):
            require(isinstance(key, bytes) and len(key) == 32, "Invalid record ID")
            record = self.records[key]
            wire = encode(record)
            require(identity(record) == key, "Record ID mismatch")
            require(decode(family(record), wire, key) == record, "Noncanonical record")
            frame_size = 1 + 32 + 4 + len(wire)
            require(len(out) + frame_size <= MAX_PACK_BYTES, "Pack exceeds budget")
            out.append(_FAMILIES.index(family(record)))
            out.extend(key)
            out.extend(len(wire).to_bytes(4, "big"))
            out.extend(wire)
        return bytes(out)

    @classmethod
    def from_bytes(cls, data) -> Bundle:
        require(isinstance(data, bytes), "Pack must be bytes")
        require(len(data) <= MAX_PACK_BYTES, "Pack exceeds budget")
        offset = 0

        def take(count):
            nonlocal offset
            require(0 <= count <= len(data) - offset, "Incomplete pack")
            value = data[offset : offset + count]
            offset += count
            return value

        require(take(len(MAGIC)) == MAGIC, "Invalid pack magic")
        count = int.from_bytes(take(4), "big")
        require(count <= MAX_RECORDS, "Excessive record count")
        require(count <= (len(data) - offset) // 37, "Incomplete pack frames")
        bundle = cls()
        previous = None
        for _ in range(count):
            tag = take(1)[0]
            require(tag < len(_FAMILIES), "Unknown record family")
            key = take(32)
            require(previous is None or previous < key, "Unsorted or duplicate ID")
            previous = key
            length = int.from_bytes(take(4), "big")
            require(length <= MAX_RECORD_BYTES, "Record exceeds budget")
            wire = take(length)
            record = decode(_FAMILIES[tag], wire, key)
            require(bundle.add(record) == key, "Claimed ID mismatch")
        require(offset == len(data), "Trailing pack data")
        return bundle

    def validate(self):
        """Check envelope/bindings/references, not source or execution semantics."""
        require(canonical(REGISTRY) == _FIXED_REGISTRY, "Registry was modified")
        # Enforce aggregate bounds even for direct edits to the public records map.
        self.pack()
        for key, declaration in _DECLARATION_BY_ID.items():
            require(self.records.get(key) == declaration, "Missing declaration Object")

        for role in _ROLES:
            for key_hex, target_hex in REGISTRY["maps"][role].items():
                target = bytes.fromhex(target_hex)
                declaration = self.records.get(target)
                require(isinstance(declaration, Object), "Registry target is not Object")
                require(
                    _DECLARATION_BY_ID.get(target) == declaration,
                    "Unknown registry declaration",
                )
                try:
                    payload = json.loads(declaration.payload)
                except (ValueError, UnicodeError) as exc:
                    raise ContractError("Invalid declaration payload") from exc
                require(
                    payload["role"] == role and payload["handle"] == key_hex,
                    "Registry declaration mismatch",
                )

        def endpoint(key, expected_kind=None):
            record = self.records.get(key)
            require(isinstance(record, Object), "Primitive endpoint must be Object")
            if expected_kind is not None:
                require(kind_of(record) == expected_kind, "Endpoint kind mismatch")
            return record

        for record in self.records.values():
            kind = kind_of(record)
            if isinstance(record, Object):
                if kind in ("declaration", "unicode-declaration"):
                    require(
                        _DECLARATION_BY_ID.get(identity(record)) == record,
                        "Undeclared declaration Object",
                    )
                elif kind == "unicode-scalar":
                    unicode_objects.validate_object(
                        record,
                        unicode_objects.EXPECTED_REGISTRY,
                    )
                elif kind not in ("source-bytes", "sequence"):
                    _canonical_payload(record.payload)
                # Local binary/domain payload semantics belong to FULL REPLAY.
            elif isinstance(record, Relation):
                endpoint(record.source)
                endpoint(record.target)
                endpoint(record.relation_type, "relation-type")
            elif isinstance(record, Derivation):
                endpoint(record.operation, "operation")
                endpoint(record.rule, "rule")
                for ref in record.inputs + record.outputs:
                    target = self.records.get(ref.identity)
                    require(target is not None, "Missing derivation reference")
                    require(
                        family(target) == ref.kind,
                        "Derivation reference family mismatch",
                    )
                    require(
                        ref.kind in ("object", "relation"),
                        "Invalid derivation reference family",
                    )
