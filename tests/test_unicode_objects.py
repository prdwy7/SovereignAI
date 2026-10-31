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
import json
import sqlite3
from dataclasses import replace

import pytest

from tools.silicate_contract import ContractError, Object
from tools.unicode_objects import (
    bootstrap,
    build,
    file_hash,
    handle,
    inspect,
    iter_ucd,
    validate_object,
    verify,
)


def line(cp, name, category="Lo"):
    return (
        ";".join([f"{cp:04X}", name, category, "0", "L", "", "", "", "", "N", "", "", "", "", ""])
        + "\n"
    )


@pytest.fixture
def source(tmp_path):
    path = tmp_path / "UnicodeData.txt"
    path.write_text(
        line(0x41, "SYNTHETIC ENGINEERING FIXTURE", "Lu")
        + line(0x4E00, "<Test Range, First>")
        + line(0x4E02, "<Test Range, Last>")
        + line(0xD800, "<Test Surrogates, First>", "Cs")
        + line(0xDFFF, "<Test Surrogates, Last>", "Cs")
        + line(0xE000, "<Private Fixture>", "Co")
        + line(0x10000, "SUPPLEMENTARY FIXTURE")
    )
    return path


def test_full_small_collection_resolves_definitions_and_exact_coverage(tmp_path, source):
    destination = tmp_path / "objects"
    result = build(destination, source, file_hash(source))
    assert result["unicode_scalar_objects"] == 6
    assert result["declaration_objects"] == 6
    assert result["total_objects"] == 12
    assert result["excluded_surrogate_code_points"] == 2048
    assert verify(destination, source)["verified"] is True
    record = inspect(destination, 0x4E01)
    assert record["payload_hex"] == "00004e01"
    registry = json.loads((destination / "registry.json").read_text())
    for role, field in (("type", "type"), ("definition", "definition"), ("schema", "schema")):
        assert record[field] in registry["maps"][role]
    with pytest.raises(ContractError):
        inspect(destination, 0xD800)
    with pytest.raises(ContractError):
        inspect(destination, 0x42)


def test_canonical_objects_and_registry_reproducible(tmp_path, source):
    a, b = tmp_path / "first", tmp_path / "second"
    build(a, source, file_hash(source))
    build(b, source, file_hash(source))
    assert (a / "objects.bin").read_bytes() == (b / "objects.bin").read_bytes()
    assert (a / "registry.json").read_bytes() == (b / "registry.json").read_bytes()
    assert inspect(a, 0x41)["id"] == inspect(b, 0x41)["id"]
    with pytest.raises(ContractError, match="already exists"):
        build(a, source, file_hash(source))


@pytest.mark.parametrize(
    "contents",
    [
        "invalid\n",
        line(0x41, "ONE") + line(0x41, "DUPLICATE"),
        line(0x42, "ONE") + line(0x41, "REVERSED"),
        line(0x4E00, "<Test, First>"),
        line(0x4E00, "<Test, Last>"),
        line(0x4E00, "<Test, First>") + line(0x4E02, "<Other, Last>"),
        line(0x4E00, "<Test, First>") + line(0x4E02, "<Test, Last>", "Lu"),
        line(0x41, "PREFIX").replace("0041;", "0x0041;"),
        line(0x41, "SPACE").replace("0041;", " 0041;"),
        line(0xABCD, "LOWERCASE").replace("ABCD;", "abcd;"),
    ],
)
def test_malformed_ucd_rejected(tmp_path, contents):
    path = tmp_path / "bad.txt"
    path.write_text(contents)
    with pytest.raises(ContractError):
        list(iter_ucd(path))


def test_definition_schema_binding_and_scalar_validation():
    registry, declarations = bootstrap()
    assert all(validate_object(record, registry) is None for record in declarations)
    atom = Object(
        handle("type", "unicode-scalar"),
        handle("definition", "unicode-scalar"),
        handle("schema", "unicode-scalar"),
        (0x41).to_bytes(4, "big"),
    )
    assert validate_object(atom, registry) == 0x41
    for bad in (
        replace(atom, definition=bytes(32)),
        replace(atom, schema=handle("schema", "declaration")),
        replace(atom, payload=b"A"),
        replace(atom, payload=(0xD800).to_bytes(4, "big")),
    ):
        with pytest.raises(ContractError):
            validate_object(bad, registry)


def test_changed_source_or_artifacts_rejected(tmp_path, source):
    destination = tmp_path / "objects"
    with pytest.raises(ContractError, match="source hash"):
        build(destination, source, "0" * 64)
    build(destination, source, file_hash(source))
    with sqlite3.connect(destination / "index.sqlite") as database:
        database.execute("UPDATE objects SET offset=0 WHERE scalar=65")
    with pytest.raises(ContractError, match="hash mismatch"):
        verify(destination, source)


def test_invalid_lookup_and_missing_metadata_fail_cleanly(tmp_path, source):
    destination = tmp_path / "objects"
    build(destination, source, file_hash(source))
    for scalar in (-1, 0xD800, 1 << 100, True):
        with pytest.raises(ContractError, match="valid Unicode scalar"):
            inspect(destination, scalar)
    with sqlite3.connect(destination / "index.sqlite") as database:
        database.execute("DELETE FROM infrastructure_properties WHERE scalar=65")
    with pytest.raises(ContractError, match="Missing infrastructure metadata"):
        inspect(destination, 65)
    manifest_path = destination / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["file_sha256"]["index.sqlite"] = file_hash(destination / "index.sqlite")
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ContractError, match="Infrastructure properties differ"):
        verify(destination, source)
