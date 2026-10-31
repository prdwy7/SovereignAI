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
"""M1.2 persistence and CLI; engineering artifacts, never learner ingestion.

Expects tools.sequence_contract and tools.sequence_engine.
Hard exits can leave sibling .lock/.stage-* paths: review and remove these
manually before retrying; locks are never automatically bypassed. All writers
must use the same locking protocol. The demo is only an engineering fixture,
not vocabulary, subject knowledge, training data, or an evaluation answer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
import tempfile
from pathlib import Path

from tools.sequence_contract import (
    MAGIC,
    MAX_PACK_BYTES,
    MAX_RECORDS,
    MAX_SOURCE_BYTES,
    PROFILE,
    REGISTRY,
    Bundle,
    canonical,
    kind_of,
    require,
)
from tools.sequence_engine import (
    build,
    reconstruct,
    verify_bundle,
)
from tools.silicate_contract import FORMAT, ContractError, Object, encode, family

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DIRECTORY = ROOT / "data/objects/sequences/m1-2/letter"
FILES = ("records.bin", "registry.json", "report.json")
REQUIRED = set(FILES) | {"manifest.json", "index.sqlite"}
JSON_LIMIT = 262144


def read_bounded(path, maximum) -> bytes:
    require(
        type(maximum) is int and 0 <= maximum <= MAX_PACK_BYTES,
        "Invalid read byte budget",
    )
    with Path(path).open("rb") as stream:
        data = stream.read(maximum + 1)
    require(len(data) <= maximum, "File exceeds byte budget")
    return data


def index_rows(bundle):
    bundle.pack()
    require(len(bundle.records) <= MAX_RECORDS, "Excessive record count")
    offset = len(MAGIC) + 4
    rows = []
    for key, record in sorted(bundle.records.items()):
        length = len(encode(record))
        rows.append((key, family(record), offset, length))
        offset += 37 + length
    return rows


def write_index(path, bundle):
    path = Path(path)
    rows = index_rows(bundle)
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    connection = None
    try:
        connection = sqlite3.connect(path)
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute(
            "CREATE TABLE records("
            "id BLOB PRIMARY KEY, family TEXT NOT NULL, "
            "offset INTEGER NOT NULL, wire_length INTEGER NOT NULL)"
        )
        connection.executemany(
            "INSERT INTO records(id,family,offset,wire_length) VALUES(?,?,?,?)",
            rows,
        )
        connection.commit()
    except sqlite3.Error as exc:
        raise ContractError("Cannot create lookup index") from exc
    finally:
        if connection is not None:
            connection.close()


def check_index(path, bundle):
    path = Path(path)
    connection = None
    try:
        require(path.is_file() and not path.is_symlink(), "Invalid lookup file")
        require(path.stat().st_size <= MAX_PACK_BYTES, "Lookup exceeds budget")
        connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)
        require(
            connection.execute("PRAGMA integrity_check").fetchall() == [("ok",)],
            "Lookup integrity failure",
        )
        rows = connection.execute(
            "SELECT id,family,offset,wire_length FROM records ORDER BY id"
        ).fetchmany(MAX_RECORDS + 1)
        expected = index_rows(bundle)
        require(rows == expected, "Lookup rows differ")
        require(
            all(
                isinstance(row[0], bytes)
                and isinstance(row[1], str)
                and type(row[2]) is int
                and type(row[3]) is int
                for row in rows
            ),
            "Invalid lookup column types",
        )
    except (OSError, sqlite3.Error) as exc:
        raise ContractError("Missing or corrupt lookup index") from exc
    finally:
        if connection is not None:
            connection.close()


def _json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "Duplicate JSON key")
            result[key] = value
        return result

    def constant(_):
        raise ContractError("Nonfinite JSON")

    try:
        return json.loads(data, object_pairs_hook=pairs, parse_constant=constant)
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise ContractError("Invalid JSON artifact") from exc


def _description(data):
    return {"sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)}


def _manifest(data):
    return {
        "format": FORMAT,
        "profile": PROFILE,
        "files": {name: _description(data[name]) for name in FILES},
        "learner_ingestion_allowed": False,
    }


def load(directory, *, check_lookup=True):
    directory = Path(directory)
    require(
        directory.is_dir() and not directory.is_symlink(),
        "Invalid artifact directory",
    )
    allowed = REQUIRED | {"README.md"}
    names = set()
    with os.scandir(directory) as entries:
        for entry in entries:
            require(len(names) < len(allowed), "Invalid artifact set")
            require(entry.name in allowed, "Invalid artifact set")
            names.add(entry.name)
    required = REQUIRED if check_lookup else REQUIRED - {"index.sqlite"}
    require(required <= names <= allowed, "Invalid artifact set")
    for name in names:
        path = directory / name
        require(path.is_file() and not path.is_symlink(), "Invalid artifact file")
    data = {
        name: read_bounded(
            directory / name, MAX_PACK_BYTES if name == "records.bin" else JSON_LIMIT
        )
        for name in FILES
    }
    manifest_bytes = read_bounded(directory / "manifest.json", JSON_LIMIT)
    manifest = _json(manifest_bytes)
    expected = _manifest(data)
    require(
        canonical(manifest) == canonical(expected)
        and manifest_bytes == canonical(expected) + b"\n",
        "Manifest mismatch",
    )
    require(data["registry.json"] == canonical(REGISTRY) + b"\n", "Registry mismatch")
    bundle = Bundle.from_bytes(data["records.bin"])
    report = verify_bundle(bundle)
    require(
        data["report.json"] == canonical(report) + b"\n",
        "Replay report mismatch",
    )
    if check_lookup:
        check_index(directory / "index.sqlite", bundle)
    return bundle, report


def verify_directory(directory):
    return load(directory)[1]


def _sync_file(path):
    with Path(path).open("rb") as stream:
        os.fsync(stream.fileno())


def _sync_directory(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _exists(path):
    return os.path.lexists(path)


def publish(directory, bundle, report=None):
    verified = verify_bundle(bundle)
    if report is not None:
        require(canonical(report) == canonical(verified), "Supplied report mismatch")
    directory = Path(os.path.abspath(directory))
    parent = directory.parent
    parent.mkdir(parents=True, exist_ok=True)
    lock = parent / (directory.name + ".lock")
    fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    staging = None
    try:
        os.close(fd)
        require(not _exists(directory), "Destination already exists")
        staging = Path(tempfile.mkdtemp(prefix=directory.name + ".stage-", dir=parent))
        data = {
            "records.bin": bundle.pack(),
            "registry.json": canonical(REGISTRY) + b"\n",
            "report.json": canonical(verified) + b"\n",
        }
        data["manifest.json"] = canonical(_manifest(data)) + b"\n"
        for name, content in data.items():
            with (staging / name).open("xb") as stream:
                stream.write(content)
                stream.flush()
                os.fsync(stream.fileno())
        write_index(staging / "index.sqlite", bundle)
        _sync_file(staging / "index.sqlite")
        verified = verify_directory(staging)
        _sync_directory(staging)
        if os.environ.get("SOVEREIGNAI_SEQUENCE_FAILPOINT") == "before_publish":
            os._exit(73)
        require(not _exists(directory), "Destination already exists")
        os.rename(staging, directory)
        staging = None
        _sync_directory(parent)
        if os.environ.get("SOVEREIGNAI_SEQUENCE_FAILPOINT") == "after_publish":
            os._exit(74)
        return verified
    finally:
        try:
            if staging is not None:
                shutil.rmtree(staging)
        finally:
            lock.unlink()


def reindex(directory):
    directory = Path(directory)
    bundle, report = load(directory, check_lookup=False)
    target = directory / "index.sqlite"
    require(not target.is_symlink(), "Symlink lookup rejected")
    fd, name = tempfile.mkstemp(prefix=".index-", dir=directory)
    os.close(fd)
    temporary = Path(name)
    temporary.unlink()
    try:
        write_index(temporary, bundle)
        check_index(temporary, bundle)
        _sync_file(temporary)
        require(not target.is_symlink(), "Symlink lookup rejected")
        os.replace(temporary, target)
        _sync_directory(directory)
    finally:
        if _exists(temporary):
            temporary.unlink()
    return report


def _record(bundle, hex_id):
    require(
        isinstance(hex_id, str)
        and len(hex_id) == 64
        and all(c in "0123456789abcdefABCDEF" for c in hex_id),
        "Expected a 64-digit hexadecimal ID",
    )
    key = bytes.fromhex(hex_id)
    require(key in bundle.records, "Unknown record ID")
    return bundle.records[key]


def _source(bundle, report):
    record = _record(bundle, report["source_id"])
    require(
        isinstance(record, Object) and kind_of(record) == "source-bytes", "Invalid source reference"
    )
    return record.payload


def _inspect(bundle, report, hex_id):
    if hex_id is not None:
        record = _record(bundle, hex_id)
        value = {
            "family": family(record),
            "kind": kind_of(record),
            "canonical_hex": encode(record).hex(),
        }
        if isinstance(record, Object):
            value.update(
                object_type=record.object_type.hex(),
                definition=record.definition.hex(),
                schema=record.schema.hex(),
                payload_hex=record.payload.hex(),
            )
        return value
    positions = None
    if report["span_map_id"] is not None:
        span = _record(bundle, report["span_map_id"])
        require(isinstance(span, Object) and kind_of(span) == "span-map", "Invalid span reference")
        positions = _json(span.payload)
    return {
        "report": report,
        "positions": positions,
        "source_view": repr(_source(bundle, report)),
    }


def _print(value):
    print(json.dumps(value, sort_keys=True, ensure_ascii=True, allow_nan=False))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("tokenize", "compose", "inspect", "reconstruct", "verify", "reindex", "demo"):
        command = commands.add_parser(name)
        command.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
        if name in ("tokenize", "compose"):
            command.add_argument("--input", type=Path, required=True)
        elif name == "inspect":
            command.add_argument("--id")
        elif name == "reconstruct":
            command.add_argument("--output", type=Path, required=True)
            command.add_argument("--source-only", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.command in ("tokenize", "compose", "demo"):
            source = (
                b"letter" if args.command == "demo" else read_bounded(args.input, MAX_SOURCE_BYTES)
            )
            bundle, report = build(source)
            report = publish(args.directory, bundle, report)
            _print(report)
            return 2 if report["status"] == "rejected" else 0
        if args.command == "reindex":
            _print(reindex(args.directory))
            return 0
        bundle, report = load(args.directory)
        if args.command == "inspect":
            _print(_inspect(bundle, report, args.id))
        elif args.command == "reconstruct":
            content = _source(bundle, report) if args.source_only else reconstruct(bundle)
            with args.output.open("xb") as stream:
                stream.write(content)
            _print({"bytes": len(content), "source_only": args.source_only})
        else:
            _print(report)
        return 0
    except (
        ContractError,
        OSError,
        sqlite3.Error,
        UnicodeError,
        ValueError,
        TypeError,
        KeyError,
    ) as exc:
        # Escape filenames and exception text as well as source-derived metadata.
        print("unicode_sequences: " + json.dumps(str(exc), ensure_ascii=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
