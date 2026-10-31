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
"""M0.1 reference codec for the pinned Scratch V1 format; not the production kernel."""

from __future__ import annotations

import hashlib
import struct
from dataclasses import dataclass

FORMAT = "sovereign-silicate-scratch-v1-sha256"
PRIMITIVE_KINDS = ("object", "relation", "derivation")
MAX_RECORD_BYTES = 1_048_576
MAX_REFERENCES = 4096
DOMAINS = {kind: f"SILICATE_{kind.upper()}_V1".encode() for kind in PRIMITIVE_KINDS}


class ContractError(ValueError):
    """Invalid, noncanonical, oversized, or identity-mismatched record."""


@dataclass(frozen=True)
class Object:
    object_type: bytes
    definition: bytes
    schema: bytes
    payload: bytes


@dataclass(frozen=True)
class Relation:
    source: bytes
    relation_type: bytes
    target: bytes
    ordering: int | None
    context: bytes


@dataclass(frozen=True)
class Reference:
    """A nested Derivation field value, never a standalone primitive or record."""

    kind: str
    identity: bytes


@dataclass(frozen=True)
class Derivation:
    execution_class: str
    inputs: tuple[Reference, ...]
    operation: bytes
    rule: bytes
    rule_version: int
    parameters: bytes
    outputs: tuple[Reference, ...]


Record = Object | Relation | Derivation


def _id(value: bytes) -> bytes:
    if not isinstance(value, bytes) or len(value) != 32:
        raise ContractError("Identifiers must be exactly 32 bytes")
    return value


def _uint(value: int, width: int) -> bytes:
    if type(value) is not int or not 0 <= value < 1 << (8 * width):
        raise ContractError("Unsigned integer out of range")
    return value.to_bytes(width, "big")


def _blob(value: bytes) -> bytes:
    if not isinstance(value, bytes) or len(value) > MAX_RECORD_BYTES:
        raise ContractError("Invalid or oversized byte string")
    return _uint(len(value), 8) + value


def _references(values: tuple[Reference, ...]) -> bytes:
    if not isinstance(values, tuple) or len(values) > MAX_REFERENCES:
        raise ContractError("Invalid or excessive references")
    encoded = []
    for ref in values:
        if not isinstance(ref, Reference) or ref.kind not in ("object", "relation"):
            raise ContractError("Invalid reference family")
        encoded.append(bytes([ref.kind == "relation"]) + _id(ref.identity))
    return _uint(len(values), 8) + b"".join(encoded)


def family(record: Record) -> str:
    if isinstance(record, Object):
        return "object"
    if isinstance(record, Relation):
        return "relation"
    if isinstance(record, Derivation):
        return "derivation"
    raise ContractError("Unknown record family")


def encode(record: Record) -> bytes:
    if isinstance(record, Object):
        wire = (
            b"\x01"
            + _id(record.object_type)
            + _id(record.definition)
            + _id(record.schema)
            + _blob(record.payload)
        )
    elif isinstance(record, Relation):
        order = b"\x00" if record.ordering is None else b"\x01" + _uint(record.ordering, 8)
        wire = (
            b"\x01"
            + _id(record.source)
            + _id(record.relation_type)
            + _id(record.target)
            + order
            + _blob(record.context)
        )
    elif isinstance(record, Derivation):
        if record.execution_class not in ("deterministic", "attested"):
            raise ContractError("Invalid execution class")
        tag = bytes([record.execution_class == "attested"])
        wire = (
            b"\x01"
            + tag
            + _references(record.inputs)
            + _id(record.operation)
            + _id(record.rule)
            + _uint(record.rule_version, 4)
            + _blob(record.parameters)
            + _references(record.outputs)
        )
    else:
        raise ContractError("Unknown record family")
    if len(wire) > MAX_RECORD_BYTES:
        raise ContractError("Record exceeds byte budget")
    return wire


def identity(record: Record) -> bytes:
    return hashlib.sha256(DOMAINS[family(record)] + encode(record)).digest()


class _Reader:
    def __init__(self, wire: bytes):
        if not isinstance(wire, bytes) or len(wire) > MAX_RECORD_BYTES:
            raise ContractError("Invalid or oversized record")
        self.wire = wire
        self.offset = 0

    def take(self, count: int) -> bytes:
        if count < 0 or count > len(self.wire) - self.offset:
            raise ContractError("Truncated record")
        value = self.wire[self.offset : self.offset + count]
        self.offset += count
        return value

    def uint(self, width: int) -> int:
        return int.from_bytes(self.take(width), "big")

    def blob(self) -> bytes:
        return self.take(self.uint(8))

    def references(self) -> tuple[Reference, ...]:
        count = self.uint(8)
        if count > MAX_REFERENCES or count > (len(self.wire) - self.offset) // 33:
            raise ContractError("Invalid reference count")
        values = []
        for _ in range(count):
            tag = self.uint(1)
            if tag not in (0, 1):
                raise ContractError("Invalid reference tag")
            values.append(Reference(("object", "relation")[tag], self.take(32)))
        return tuple(values)

    def finish(self) -> None:
        if self.offset != len(self.wire):
            raise ContractError("Trailing bytes")


def decode(kind: str, wire: bytes, expected_id: bytes | None = None) -> Record:
    """Decode one complete record; record family and profile belong to the outer envelope."""
    if kind not in DOMAINS:
        raise ContractError("Unknown record family")
    reader = _Reader(wire)
    if reader.uint(1) != 1:
        raise ContractError("Unsupported protocol version")
    record: Record
    if kind == "object":
        record = Object(reader.take(32), reader.take(32), reader.take(32), reader.blob())
    elif kind == "relation":
        source, relation_type, target = reader.take(32), reader.take(32), reader.take(32)
        tag = reader.uint(1)
        if tag not in (0, 1):
            raise ContractError("Invalid ordering tag")
        ordering = reader.uint(8) if tag else None
        record = Relation(source, relation_type, target, ordering, reader.blob())
    else:
        tag = reader.uint(1)
        if tag not in (0, 1):
            raise ContractError("Invalid execution class")
        execution = ("deterministic", "attested")[tag]
        inputs = reader.references()
        operation, rule, version = reader.take(32), reader.take(32), reader.uint(4)
        params = reader.blob()
        record = Derivation(
            execution, inputs, operation, rule, version, params, reader.references()
        )
    reader.finish()
    if encode(record) != wire:
        raise ContractError("Noncanonical record")
    if expected_id is not None and identity(record) != _id(expected_id):
        raise ContractError("Claimed identity mismatch")
    return record


def ordered_payload(children: tuple[bytes, ...]) -> bytes:
    """M0 fixture payload contract: count followed by ordered 32-byte child IDs."""
    if not isinstance(children, tuple) or len(children) > MAX_REFERENCES:
        raise ContractError("Invalid child count")
    return struct.pack(">Q", len(children)) + b"".join(_id(child) for child in children)
