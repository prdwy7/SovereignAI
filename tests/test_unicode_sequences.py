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
"""Engineering-only fixtures: never learner data, seeds, or evaluation answers."""

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

from tools import unicode_sequences as api
from tools.sequence_contract import canonical
from tools.sequence_engine import build, reconstruct
from tools.silicate_contract import (
    ContractError,
    Derivation,
    Object,
    Relation,
    decode,
    encode,
    family,
)

FAILPOINT = "SOVEREIGNAI_SEQUENCE_FAILPOINT"
CANONICAL = ("records.bin", "registry.json", "report.json", "manifest.json")


def cli(*args, failpoint=None):
    env = os.environ.copy()
    env.pop(FAILPOINT, None)
    if failpoint:
        env[FAILPOINT] = failpoint
    return subprocess.run(
        [sys.executable, "-m", "tools.unicode_sequences", *map(str, args)],
        cwd=api.ROOT,
        env=env,
        capture_output=True,
        timeout=60,
    )


def snapshot(path):
    return {p.name: p.read_bytes() for p in path.iterdir() if p.is_file()}


def canonical_bytes(path):
    return {name: (path / name).read_bytes() for name in CANONICAL}


def create(path, source=b"letter"):
    bundle, report = build(source)
    assert api.publish(path, bundle, report) == report
    return bundle, report


def rewrite_manifest(path):
    # Deliberately recompute hashes independently, not through api._manifest.
    manifest = json.loads((path / "manifest.json").read_bytes())
    for name in api.FILES:
        data = (path / name).read_bytes()
        manifest["files"][name] = {
            "sha256": hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        }
    (path / "manifest.json").write_bytes(canonical(manifest) + b"\n")


@pytest.mark.parametrize("source,accepted", [(b"letter", True), (b"\xff\x00", False)])
def test_publish_reopen_seek_and_reconstruct(tmp_path, source, accepted):
    path = tmp_path / "artifact"
    bundle, report = create(path, source)
    reopened, replay = api.load(path)
    assert replay == report
    assert report["status"] == ("accepted" if accepted else "rejected")
    assert report["learner_ingestion_allowed"] is False
    assert reopened.records == bundle.records
    assert set(map(type, reopened.records.values())) <= {Object, Relation, Derivation}
    if accepted:
        assert set(map(type, reopened.records.values())) == {
            Object,
            Relation,
            Derivation,
        }
        assert reconstruct(reopened) == source
        assert bytes.fromhex(report["sequence_id"]) in reopened.records
    else:
        with pytest.raises(ContractError):
            reconstruct(reopened)

    with sqlite3.connect(path / "index.sqlite") as db:
        rows = db.execute("SELECT id,family,offset,wire_length FROM records ORDER BY id").fetchall()
    assert [row[0] for row in rows] == sorted(bundle.records)
    offset = len(api.MAGIC) + 4
    with (path / "records.bin").open("rb") as stream:
        for key, fam, actual_offset, length in rows:
            record = bundle.records[key]
            wire = encode(record)
            assert (fam, actual_offset, length) == (family(record), offset, len(wire))
            stream.seek(actual_offset + 37)
            stored = stream.read(length)
            assert stored == wire
            assert decode(fam, stored, key) == record
            offset += 37 + length
        assert offset == (path / "records.bin").stat().st_size

    output = tmp_path / "reconstructed"
    result = cli("reconstruct", "--directory", path, "--output", output)
    assert result.returncode == (0 if accepted else 1), result.stderr
    if accepted:
        assert output.read_bytes() == source
    else:
        assert not output.exists()
    raw = tmp_path / "raw"
    result = cli("reconstruct", "--directory", path, "--output", raw, "--source-only")
    assert result.returncode == 0, result.stderr
    assert raw.read_bytes() == source
    before = raw.read_bytes()
    assert cli("reconstruct", "--directory", path, "--output", raw, "--source-only").returncode == 1
    assert raw.read_bytes() == before


def test_independent_build_copy_restore(tmp_path):
    first, second, copied, restored = [tmp_path / n for n in ("a", "b", "c", "d")]
    a, report = create(first)
    b, other = create(second)
    assert report == other
    assert sorted(a.records) == sorted(b.records)
    assert canonical_bytes(first) == canonical_bytes(second)
    shutil.copytree(first, copied)
    shutil.copytree(copied, restored)
    for path in (copied, restored):
        loaded, replay = api.load(path)
        assert replay == report
        assert sorted(loaded.records) == sorted(a.records)
        assert canonical_bytes(path) == canonical_bytes(first)


@pytest.mark.parametrize("damage", ["missing", "corrupt", "oversized", "offset"])
def test_reindex_only_changes_index(tmp_path, damage):
    path = tmp_path / "artifact"
    bundle, report = create(path)
    before = canonical_bytes(path)
    index = path / "index.sqlite"
    if damage == "missing":
        index.unlink()
    elif damage == "corrupt":
        index.write_bytes(b"not sqlite")
    elif damage == "oversized":
        with index.open("wb") as stream:
            stream.truncate(api.MAX_PACK_BYTES + 1)
    else:
        with sqlite3.connect(index) as db:
            db.execute("UPDATE records SET offset=offset+1")
    with pytest.raises(ContractError):
        api.load(path)
    assert api.reindex(path) == report
    loaded, replay = api.load(path)
    assert loaded.records == bundle.records
    assert replay == report
    assert canonical_bytes(path) == before


@pytest.mark.parametrize("name", CANONICAL)
def test_framing_or_hash_tamper(tmp_path, name):
    path = tmp_path / "artifact"
    create(path)
    target = path / name
    target.write_bytes(target.read_bytes() + b" ")
    with pytest.raises(ContractError):
        api.load(path)


@pytest.mark.parametrize("name", ["registry.json", "report.json"])
def test_hash_valid_semantic_tamper(tmp_path, name):
    path = tmp_path / "artifact"
    create(path)
    target = path / name
    value = json.loads(target.read_bytes())
    assert isinstance(value, dict)
    value["engineering_tamper"] = True
    target.write_bytes(canonical(value) + b"\n")
    rewrite_manifest(path)
    with pytest.raises(ContractError):
        api.load(path)
    with pytest.raises(ContractError):
        api.reindex(path)


def test_manifest_boolean_not_integer(tmp_path):
    path = tmp_path / "artifact"
    create(path)
    target = path / "manifest.json"
    value = json.loads(target.read_bytes())
    value["learner_ingestion_allowed"] = 0
    target.write_bytes(canonical(value) + b"\n")
    with pytest.raises(ContractError):
        api.load(path)


@pytest.mark.parametrize("name", CANONICAL)
def test_missing_canonical_cannot_reindex(tmp_path, name):
    path = tmp_path / "artifact"
    create(path)
    (path / name).unlink()
    before = snapshot(path)
    with pytest.raises(ContractError):
        api.reindex(path)
    assert snapshot(path) == before


@pytest.mark.parametrize("mode", ["unexpected", "canonical-link", "index-link"])
def test_unexpected_and_symlink_rejected(tmp_path, mode):
    path = tmp_path / "artifact"
    create(path)
    outside = tmp_path / "external"
    outside.write_bytes(b"external sentinel")
    if mode == "unexpected":
        (path / "unexpected").write_bytes(b"fixture")
    else:
        target = path / ("index.sqlite" if mode == "index-link" else "report.json")
        target.unlink()
        target.symlink_to(outside)
    with pytest.raises(ContractError):
        api.load(path)
    with pytest.raises(ContractError):
        api.reindex(path)
    assert outside.read_bytes() == b"external sentinel"


def test_no_overwrite_and_bounded_read(tmp_path):
    path = tmp_path / "artifact"
    original, _ = create(path)
    before = snapshot(path)
    for bundle in (original, build(b"x")[0]):
        with pytest.raises(ContractError):
            api.publish(path, bundle)
        assert snapshot(path) == before
    source = tmp_path / "source"
    source.write_bytes(b"1234")
    assert api.read_bounded(source, 4) == b"1234"
    with pytest.raises(ContractError):
        api.read_bounded(source, 3)
    assert source.read_bytes() == b"1234"


def test_cli_status_input_and_alias(tmp_path):
    source = tmp_path / "source"
    source.write_bytes(b"letter")
    a, b = tmp_path / "a", tmp_path / "b"
    assert cli("tokenize", "--input", source, "--directory", a).returncode == 0
    assert cli("compose", "--input", source, "--directory", b).returncode == 0
    assert canonical_bytes(a) == canonical_bytes(b)
    assert source.read_bytes() == b"letter"
    source.write_bytes(b"\xff")
    rejected = tmp_path / "rejected"
    assert cli("tokenize", "--input", source, "--directory", rejected).returncode == 2
    assert source.read_bytes() == b"\xff"
    with source.open("wb") as stream:
        stream.truncate(api.MAX_SOURCE_BYTES + 1)
    size = source.stat().st_size
    digest = hashlib.sha256(source.read_bytes()).digest()
    destination = tmp_path / "oversized"
    assert cli("tokenize", "--input", source, "--directory", destination).returncode == 1
    assert not destination.exists()
    assert source.stat().st_size == size
    assert hashlib.sha256(source.read_bytes()).digest() == digest
    assert cli("tokenize", "--directory", tmp_path / "invalid").returncode == 2
    assert cli("unknown", "--directory", tmp_path / "unknown").returncode == 2


def test_inspect_json_and_exact_record(tmp_path):
    path = tmp_path / "artifact"
    bundle, report = create(path, b"\x00\xe2\x80\xae")
    result = cli("inspect", "--directory", path)
    assert result.returncode == 0, result.stderr
    text = result.stdout.decode("ascii")
    json.loads(text)
    assert all(ord(c) >= 32 for c in text.rstrip("\n"))
    assert "\x00" not in text and "\u202e" not in text
    key = report["source_id"]
    record = bundle.records[bytes.fromhex(key)]
    result = cli("inspect", "--directory", path, "--id", key)
    assert result.returncode == 0, result.stderr
    value = json.loads(result.stdout)
    assert value["canonical_hex"] == encode(record).hex()
    assert value["definition"] == record.definition.hex()
    assert value["schema"] == record.schema.hex()
    for invalid in ("bad", "00" * 32):
        if invalid != key:
            assert cli("inspect", "--directory", path, "--id", invalid).returncode == 1


@pytest.mark.parametrize("point,code", [("before_publish", 73), ("after_publish", 74)])
def test_hard_exit_recovery(tmp_path, point, code):
    source = tmp_path / "source"
    source.write_bytes(b"letter")
    path = tmp_path / "artifact"
    args = ("tokenize", "--input", source, "--directory", path)
    assert cli(*args, failpoint=point).returncode == code
    lock = tmp_path / "artifact.lock"
    assert lock.is_file()
    stages = list(tmp_path.glob("artifact.stage-*"))
    if point == "before_publish":
        assert not path.exists()
        assert len(stages) == 1
        assert api.verify_directory(stages[0])["status"] == "accepted"
        assert cli(*args).returncode == 1
        for stage in stages:
            assert stage.parent == tmp_path and not stage.is_symlink()
            shutil.rmtree(stage)
        lock.unlink()
        assert cli(*args).returncode == 0
    else:
        assert not stages
        before = snapshot(path)
        assert cli("verify", "--directory", path).returncode == 0
        assert lock.exists()
        lock.unlink()
        assert cli(*args).returncode == 1
        assert snapshot(path) == before


def test_staging_exception_cleanup(tmp_path, monkeypatch):
    path = tmp_path / "artifact"
    bundle, _ = build(b"letter")
    monkeypatch.delenv(FAILPOINT, raising=False)

    def fail(directory):
        assert Path(directory).parent == tmp_path
        raise RuntimeError("engineering injected verification failure")

    monkeypatch.setattr(api, "verify_directory", fail)
    with pytest.raises(RuntimeError):
        api.publish(path, bundle)
    assert not path.exists()
    assert not (tmp_path / "artifact.lock").exists()
    assert not list(tmp_path.glob("artifact.stage-*"))


def test_exclusive_owned_lock_contention(tmp_path):
    path = tmp_path / "artifact"
    lock = tmp_path / "artifact.lock"
    source = tmp_path / "source"
    source.write_bytes(b"letter")
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(fd)
    try:
        assert cli("tokenize", "--input", source, "--directory", path).returncode == 1
        assert not path.exists()
        assert lock.exists()
        assert not list(tmp_path.glob("artifact.stage-*"))
    finally:
        lock.unlink()
    assert cli("tokenize", "--input", source, "--directory", path).returncode == 0
