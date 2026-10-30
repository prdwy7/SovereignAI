"""M1.1: reproducible Unicode scalar Objects, declaration Objects, and a local lookup index."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sqlite3
import struct
import tempfile
from datetime import UTC, datetime
from functools import cache
from itertools import zip_longest
from pathlib import Path

from tools.silicate_contract import (
    FORMAT,
    MAX_RECORD_BYTES,
    ContractError,
    Object,
    decode,
    encode,
    identity,
)

ROOT = Path(__file__).resolve().parent.parent
UCD_ROOT = ROOT / "data/unicode/18.0.0"
DEFAULT_DESTINATION = ROOT / "data/objects/unicode/18.0.0"
BOOTSTRAP_PROFILE = "sovereign-unicode-object-bootstrap-v1"
MAGIC = b"SOVOBJ1\n"


def canonical_json(value: dict) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def scalar_valid(value: int) -> bool:
    return type(value) is int and 0 <= value <= 0x10FFFF and not 0xD800 <= value <= 0xDFFF


@cache
def handle(role: str, name: str) -> bytes:
    return hashlib.sha256(f"{BOOTSTRAP_PROFILE}:{role}:{name}".encode()).digest()


def bootstrap() -> tuple[dict, list[Object]]:
    """Finite engineering declarations; typed handles resolve to actual declaration Objects."""
    specs = {
        ("type", "declaration"): {"purpose": "engineering declaration"},
        ("type", "unicode-scalar"): {"purpose": "opaque Unicode scalar atom"},
        ("definition", "declaration"): {"meaning": "bootstrap registry declaration"},
        ("definition", "unicode-scalar"): {"meaning": "scalar identity only", "unicode": "18.0.0"},
        ("schema", "declaration"): {"encoding": "canonical-json", "profile": BOOTSTRAP_PROFILE},
        ("schema", "unicode-scalar"): {
            "encoding": "unsigned-big-endian",
            "bytes": 4,
            "maximum": 0x10FFFF,
            "excluded": [0xD800, 0xDFFF],
        },
    }
    records = []
    registry = {
        "profile": BOOTSTRAP_PROFILE,
        "format": FORMAT,
        "maps": {role: {} for role in ("type", "definition", "schema")},
    }
    for (role, name), spec in specs.items():
        key = handle(role, name)
        payload = canonical_json({"role": role, "name": name, "handle": key.hex(), "spec": spec})
        record = Object(
            handle("type", "declaration"),
            handle("definition", "declaration"),
            handle("schema", "declaration"),
            payload,
        )
        records.append(record)
        registry["maps"][role][key.hex()] = identity(record).hex()
    return registry, records


EXPECTED_REGISTRY, DECLARATION_RECORDS = bootstrap()


def validate_object(record: Object, registry: dict) -> int | None:
    if not isinstance(record, Object):
        raise ContractError("Unicode collection accepts Object records only")
    if registry != EXPECTED_REGISTRY:
        raise ContractError("Unrecognized bootstrap registry")
    for role, key in (
        ("type", record.object_type),
        ("definition", record.definition),
        ("schema", record.schema),
    ):
        if key.hex() not in registry["maps"][role]:
            raise ContractError("Unresolved declaration handle")
    atom_binding = tuple(
        handle(role, "unicode-scalar") for role in ("type", "definition", "schema")
    )
    if (record.object_type, record.definition, record.schema) == atom_binding:
        if len(record.payload) != 4:
            raise ContractError("Scalar payload must be four bytes")
        scalar = int.from_bytes(record.payload, "big")
        if not scalar_valid(scalar):
            raise ContractError("Invalid Unicode scalar payload")
        return scalar
    if record not in DECLARATION_RECORDS:
        raise ContractError("Unknown declaration or invalid type/definition/schema binding")
    return None


def iter_ucd(path: Path):
    """Expand First/Last records; reject malformed, duplicated and unordered source records."""
    pending = None
    previous = -1
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            fields = line.rstrip("\n\r").split(";")
            if len(fields) != 15:
                raise ContractError(f"UCD field count at line {line_number}")
            if re.fullmatch(r"[0-9A-F]{4,6}", fields[0]) is None:
                raise ContractError(f"Noncanonical UCD code-point field at line {line_number}")
            try:
                cp = int(fields[0], 16)
            except ValueError:
                raise ContractError(f"Invalid UCD code point at line {line_number}") from None
            if not previous < cp <= 0x10FFFF:
                raise ContractError("UCD code points must be unique and increasing")
            previous = cp
            name = fields[1]
            if name.endswith(", First>"):
                if pending is not None:
                    raise ContractError("Nested UCD range")
                pending = cp, fields
            elif name.endswith(", Last>"):
                if pending is None:
                    raise ContractError("UCD Last record without First")
                start, first = pending
                if first[1].removesuffix(", First>") != name.removesuffix(", Last>"):
                    raise ContractError("Mismatched UCD range name")
                if first[2:] != fields[2:] or start >= cp:
                    raise ContractError("Mismatched UCD range properties")
                for value in range(start, cp + 1):
                    yield value, first[1], first[2]
                pending = None
            else:
                if pending is not None:
                    raise ContractError("Unclosed UCD range")
                yield cp, name, fields[2]
    if pending is not None:
        raise ContractError("Unclosed UCD range")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def source_digest() -> str:
    manifest = json.loads((UCD_ROOT / "manifest.json").read_text())
    if manifest["unicode_version"] != "18.0.0":
        raise ContractError("Wrong Unicode source version")
    return next(f["sha256"] for f in manifest["files"] if f["path"] == "ucd/UnicodeData.txt")


def read_frame(stream) -> tuple[int, bytes, bytes] | None:
    offset = stream.tell()
    prefix = stream.read(4)
    if not prefix:
        return None
    if len(prefix) != 4:
        raise ContractError("Truncated frame length")
    length = int.from_bytes(prefix, "big")
    if not 105 <= length <= MAX_RECORD_BYTES:
        raise ContractError("Invalid Object frame length")
    claimed_id, wire = stream.read(32), stream.read(length)
    if len(claimed_id) != 32 or len(wire) != length:
        raise ContractError("Truncated Object frame")
    return offset, claimed_id, wire


def connect_readonly(path: Path):
    return sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)


def verify(destination: Path, ucd_path: Path) -> dict:
    manifest = json.loads((destination / "manifest.json").read_text())
    if (
        manifest["format"] != FORMAT
        or manifest["bootstrap_profile"] != BOOTSTRAP_PROFILE
        or manifest["unicode_version"] != "18.0.0"
    ):
        raise ContractError("Collection format mismatch")
    if set(manifest["file_sha256"]) != {"objects.bin", "index.sqlite", "registry.json"}:
        raise ContractError("Unexpected collection file set")
    if file_hash(ucd_path) != manifest["source_sha256"]:
        raise ContractError("Unicode source hash mismatch")
    for name, digest in manifest["file_sha256"].items():
        if file_hash(destination / name) != digest:
            raise ContractError(f"Collection hash mismatch: {name}")
    registry = json.loads((destination / "registry.json").read_text())
    if registry != bootstrap()[0]:
        raise ContractError("Registry differs from bootstrap contract")
    expected = {cp for cp, _, _ in iter_ucd(ucd_path) if scalar_valid(cp)}
    seen = set()
    declaration_ids = set()
    count = 0
    with connect_readonly(destination / "index.sqlite") as database:
        if database.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise ContractError("Index integrity failure")
        with (destination / "objects.bin").open("rb") as stream:
            if stream.read(len(MAGIC)) != MAGIC:
                raise ContractError("Collection header mismatch")
            while (frame := read_frame(stream)) is not None:
                offset, claimed_id, wire = frame
                record = decode("object", wire, claimed_id)
                scalar = validate_object(record, registry)
                entry = database.execute(
                    "SELECT scalar, offset, wire_length FROM objects WHERE id=?", (claimed_id,)
                ).fetchone()
                if entry != (scalar, offset, len(wire)):
                    raise ContractError("Index does not match canonical collection")
                if scalar is None:
                    if claimed_id in declaration_ids:
                        raise ContractError("Duplicate declaration Object")
                    declaration_ids.add(claimed_id)
                else:
                    if scalar in seen:
                        raise ContractError("Duplicate scalar Object")
                    seen.add(scalar)
                count += 1
        if count != database.execute("SELECT count(*) FROM objects").fetchone()[0]:
            raise ContractError("Index has missing or extra records")
        expected_properties = (
            (cp, name, category) for cp, name, category in iter_ucd(ucd_path) if scalar_valid(cp)
        )
        stored_properties = database.execute(
            "SELECT scalar, source_name, category FROM infrastructure_properties ORDER BY scalar"
        )
        for expected_property, stored_property in zip_longest(
            expected_properties, stored_properties
        ):
            if expected_property != stored_property:
                raise ContractError("Infrastructure properties differ from the Unicode source")
    wanted_declarations = {identity(record) for record in bootstrap()[1]}
    if seen != expected or declaration_ids != wanted_declarations:
        raise ContractError("Source coverage or declaration-reference resolution failed")
    if count != manifest["total_objects"] or len(seen) != manifest["unicode_scalar_objects"]:
        raise ContractError("Manifest counts do not match records")
    return {
        "verified": True,
        "unicode_scalar_objects": len(seen),
        "declaration_objects": len(declaration_ids),
        "total_objects": count,
    }


def build(destination: Path, ucd_path: Path, expected_sha256: str) -> dict:
    if destination.exists():
        raise ContractError("Destination already exists; existing Objects will not be overwritten")
    if file_hash(ucd_path) != expected_sha256:
        raise ContractError("Unicode source hash mismatch")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".unicode-build-", dir=destination.parent))
    registry, declarations = bootstrap()
    (staging / "registry.json").write_bytes(canonical_json(registry) + b"\n")
    scalar_count, surrogate_count = 0, 0
    with (
        sqlite3.connect(staging / "index.sqlite") as database,
        (staging / "objects.bin").open("wb") as stream,
    ):
        database.execute("PRAGMA user_version=1")
        database.execute(
            "CREATE TABLE objects (id BLOB PRIMARY KEY, scalar INTEGER UNIQUE, offset INTEGER NOT NULL, wire_length INTEGER NOT NULL)"
        )
        database.execute(
            "CREATE TABLE infrastructure_properties (scalar INTEGER PRIMARY KEY, source_name TEXT NOT NULL, category TEXT NOT NULL)"
        )
        stream.write(MAGIC)

        def store(record: Object, scalar: int | None) -> None:
            if validate_object(record, registry) != scalar:
                raise ContractError("Object failed definition/schema validation")
            wire, identifier = encode(record), identity(record)
            offset = stream.tell()
            stream.write(struct.pack(">I", len(wire)) + identifier + wire)
            database.execute(
                "INSERT INTO objects VALUES (?, ?, ?, ?)", (identifier, scalar, offset, len(wire))
            )

        for record in declarations:
            store(record, None)
        for cp, name, category in iter_ucd(ucd_path):
            if not scalar_valid(cp):
                surrogate_count += 1
                continue
            atom = Object(
                handle("type", "unicode-scalar"),
                handle("definition", "unicode-scalar"),
                handle("schema", "unicode-scalar"),
                cp.to_bytes(4, "big"),
            )
            store(atom, cp)
            database.execute(
                "INSERT INTO infrastructure_properties VALUES (?, ?, ?)", (cp, name, category)
            )
            scalar_count += 1
    manifest = {
        "build": "M1.1",
        "format": FORMAT,
        "bootstrap_profile": BOOTSTRAP_PROFILE,
        "unicode_version": "18.0.0",
        "source": "UnicodeData.txt with First/Last ranges expanded",
        "source_sha256": expected_sha256,
        "unicode_scalar_objects": scalar_count,
        "declaration_objects": len(declarations),
        "total_objects": scalar_count + len(declarations),
        "excluded_surrogate_code_points": surrogate_count,
        "repertoire": "Assigned scalar records in UCD, including controls and private-use ranges; unassigned scalars are not materialized",
        "payload": "4-byte unsigned big-endian scalar value; no names or linguistic meanings",
        "storage": "objects.bin holds canonical Object frames; index.sqlite is a rebuildable lookup and infrastructure metadata view",
        "file_sha256": {
            name: file_hash(staging / name)
            for name in ("objects.bin", "index.sqlite", "registry.json")
        },
        "sqlite_version": sqlite3.sqlite_version,
        "implementation_sha256": file_hash(Path(__file__)),
        "created_at": datetime.now(UTC).isoformat(),
        "reproducibility": "Canonical object bytes, IDs, registry and record ordering are deterministic; SQLite bytes and timestamps are environment-specific",
    }
    (staging / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    result = verify(staging, ucd_path)
    manifest["verification"] = result
    (staging / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    os.rename(staging, destination)
    return manifest


def inspect(destination: Path, scalar: int) -> dict:
    if not scalar_valid(scalar):
        raise ContractError("Inspection requires a valid Unicode scalar")
    registry = json.loads((destination / "registry.json").read_text())
    with connect_readonly(destination / "index.sqlite") as database:
        entry = database.execute(
            "SELECT id, offset FROM objects WHERE scalar=?", (scalar,)
        ).fetchone()
        if entry is None:
            raise ContractError("Scalar is not materialized in this collection")
        metadata = database.execute(
            "SELECT source_name, category FROM infrastructure_properties WHERE scalar=?", (scalar,)
        ).fetchone()
        if metadata is None:
            raise ContractError("Missing infrastructure metadata for scalar")
    with (destination / "objects.bin").open("rb") as stream:
        stream.seek(entry[1])
        frame = read_frame(stream)
    if frame is None or frame[1] != entry[0]:
        raise ContractError("Invalid lookup frame")
    record = decode("object", frame[2], entry[0])
    if validate_object(record, registry) != scalar:
        raise ContractError("Lookup scalar mismatch")
    return {
        "scalar": f"U+{scalar:04X}",
        "id": entry[0].hex(),
        "type": record.object_type.hex(),
        "definition": record.definition.hex(),
        "schema": record.schema.hex(),
        "payload_hex": record.payload.hex(),
        "infrastructure_only": {"source_name": metadata[0], "category": metadata[1]},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("build", "verify", "inspect"))
    parser.add_argument("--directory", type=Path, default=DEFAULT_DESTINATION)
    parser.add_argument("--scalar", help="For inspect: U+0041 or hexadecimal 0041")
    args = parser.parse_args()
    try:
        if args.command == "build":
            result = build(args.directory, UCD_ROOT / "ucd/UnicodeData.txt", source_digest())
        elif args.command == "verify":
            result = verify(args.directory, UCD_ROOT / "ucd/UnicodeData.txt")
        else:
            if args.scalar is None:
                parser.error("inspect requires --scalar")
            result = inspect(args.directory, int(args.scalar.removeprefix("U+"), 16))
        print(json.dumps(result, indent=2))
    except (ContractError, OSError, ValueError, sqlite3.Error) as exc:
        print(f"Unicode Object operation failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
