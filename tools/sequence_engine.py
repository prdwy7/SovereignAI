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
"""M1.2 bounded sequence engine; local verification required.

Only Object, Relation, and Derivation persist. Unicode names/properties are
never copied into artifacts. This module supplies no vocabulary, subject
knowledge, teacher seeds, evaluation answers, or mastery assessments.

repertoire() assumes its pinned input remains unchanged for the process
lifetime after the first successful call. Clear its cache or restart after
changing that input. iter_ucd(path) supplies expanded rows with scalar first.

Strings containing surrogates fail at the build_text API boundary: they have
no original strict-UTF-8 source bytes to preserve as a rejected import.
"""

from __future__ import annotations

import hashlib
import sqlite3
from functools import cache

from tools import unicode_objects
from tools.sequence_contract import (
    DECLARATIONS,
    MAX_SCALARS,
    MAX_SOURCE_BYTES,
    PROFILE,
    Bundle,
    canonical,
    jobj,
    kind_of,
    obj,
    require,
)
from tools.silicate_contract import (
    ContractError,
    Derivation,
    Object,
    Reference,
    Relation,
    family,
    identity,
    ordered_payload,
)

UCD_SHA256 = "0736451de439ae7baf1425136617da495e09ee5afbe6e394374db7009ea08950"


@cache
def repertoire() -> frozenset[int]:
    """Validate the pinned file before expanding its assigned scalar ranges."""
    path = unicode_objects.UCD_ROOT / "ucd/UnicodeData.txt"
    try:
        digest = unicode_objects.file_hash(path)
        require(digest == UCD_SHA256, "UnicodeData hash mismatch")
        return frozenset(
            row[0] for row in unicode_objects.iter_ucd(path) if unicode_objects.scalar_valid(row[0])
        )
    except ContractError:
        raise
    except (OSError, ValueError, TypeError, IndexError) as exc:
        raise ContractError("Cannot load pinned Unicode repertoire") from exc


def _scalar_object(cp: int) -> Object:
    return Object(
        *(
            unicode_objects.handle(role, "unicode-scalar")
            for role in ("type", "definition", "schema")
        ),
        cp.to_bytes(4, "big"),
    )


def _check_collection(cp: int, record: Object) -> None:
    """Compare canonical atom fields, not SQLite offsets or metadata."""
    expected = {
        "id": identity(record).hex(),
        "type": record.object_type.hex(),
        "definition": record.definition.hex(),
        "schema": record.schema.hex(),
        "payload_hex": record.payload.hex(),
    }
    try:
        actual = unicode_objects.inspect(unicode_objects.DEFAULT_DESTINATION, cp)
        require(isinstance(actual, dict), "Invalid Collection lookup")
        require(
            all(actual.get(key) == value for key, value in expected.items()),
            "Collection scalar Object mismatch",
        )
    except ContractError:
        raise
    except (OSError, sqlite3.Error, ValueError, TypeError, KeyError) as exc:
        raise ContractError("Collection lookup failed") from exc


def _error(code: str, start: int, end: int, index: int | None, cp: int | None = None) -> dict:
    value = {
        "code": code,
        "byte_start": start,
        "byte_end": end,
        "scalar_index": index,
    }
    if cp is not None:
        value["scalar"] = f"U+{cp:04X}"
    return value


def build(data: bytes, *, use_collection=True) -> tuple[Bundle, dict]:
    """Build an engineering envelope; only structural validation occurs here.

    Rejection precedence is malformed UTF-8, scalar count, then repertoire.
    Collection lookup occurs only after the entire input passes those checks.
    """
    require(type(data) is bytes, "Source must be exact bytes")
    require(len(data) <= MAX_SOURCE_BYTES, "Source exceeds byte limit")
    require(type(use_collection) is bool, "use_collection must be bool")

    error = None
    text = None
    positions = []
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        error = _error("invalid-utf8", exc.start, exc.end, None)

    if text is not None:
        offset = 0
        for index, char in enumerate(text):
            end = offset + len(char.encode("utf-8", errors="strict"))
            positions.append((index, offset, end, ord(char)))
            offset = end
        require(offset == len(data), "UTF-8 span coverage mismatch")
        if len(positions) > MAX_SCALARS:
            index, start, end, _ = positions[MAX_SCALARS]
            error = _error("scalar-limit", start, end, index)
        else:
            assigned = repertoire()
            for index, start, end, cp in positions:
                if cp not in assigned:
                    error = _error("unsupported-scalar", start, end, index, cp)
                    break

    accepted = error is None
    bundle = Bundle()
    for declaration in DECLARATIONS:
        bundle.add(declaration)
    source_id = bundle.add(obj("source-bytes", data))
    operation_id = bundle.add(
        jobj(
            "operation",
            {
                "name": "tokenize-compose",
                "profile": PROFILE,
            },
        )
    )
    rule_id = bundle.add(
        jobj(
            "rule",
            {
                "name": "strict-utf8-assigned-scalars",
                "version": 1,
                "unicode_source_sha256": UCD_SHA256,
            },
        )
    )
    member_type_id = bundle.add(
        jobj(
            "relation-type",
            {
                "name": "ordered-member",
                "profile": PROFILE,
            },
        )
    )

    scalar_ids = {}
    ordered_ids = ()
    sequence_id = None
    span_id = None
    memberships = []
    if accepted:
        for _, _, _, cp in positions:
            if cp not in scalar_ids:
                record = _scalar_object(cp)
                if use_collection:
                    _check_collection(cp, record)
                scalar_ids[cp] = bundle.add(record)
        ordered_ids = tuple(scalar_ids[cp] for _, _, _, cp in positions)
        sequence_id = bundle.add(obj("sequence", ordered_payload(ordered_ids)))
        for index, child_id in enumerate(ordered_ids):
            memberships.append(
                bundle.add(
                    Relation(
                        sequence_id,
                        member_type_id,
                        child_id,
                        index,
                        b"",
                    )
                )
            )
        span_id = bundle.add(
            jobj(
                "span-map",
                {
                    "source": source_id.hex(),
                    "sequence": sequence_id.hex(),
                    "positions": [
                        {
                            "index": index,
                            "byte_start": start,
                            "byte_end": end,
                            "scalar": cp,
                            "object": scalar_ids[cp].hex(),
                        }
                        for index, start, end, cp in positions
                    ],
                },
            )
        )

    status = "accepted" if accepted else "rejected"
    result_value = {
        "profile": PROFILE,
        "status": status,
        "source": source_id.hex(),
        "sequence": sequence_id.hex() if sequence_id is not None else None,
        "span_map": span_id.hex() if span_id is not None else None,
        "error": error,
        "unicode_source_sha256": UCD_SHA256,
    }
    result_id = bundle.add(jobj("result", result_value))
    outputs = (
        (
            Reference("object", sequence_id),
            Reference("object", span_id),
            Reference("object", result_id),
        )
        + tuple(Reference("relation", key) for key in memberships)
        if accepted
        else (Reference("object", result_id),)
    )
    derivation_id = bundle.add(
        Derivation(
            execution_class="deterministic",
            inputs=(Reference("object", source_id),)
            + tuple(Reference("object", key) for key in ordered_ids),
            operation=operation_id,
            rule=rule_id,
            rule_version=1,
            parameters=canonical({"profile": PROFILE}),
            outputs=outputs,
        )
    )
    bundle.validate()
    counts = dict.fromkeys(("object", "relation", "derivation"), 0)
    for record in bundle.records.values():
        counts[family(record)] += 1
    # Result fields, rather than uncommitted source annotations, drive report.
    report = {
        "profile": result_value["profile"],
        "status": result_value["status"],
        "source_id": result_value["source"],
        "sequence_id": result_value["sequence"],
        "span_map_id": result_value["span_map"],
        "result_id": result_id.hex(),
        "derivation_id": derivation_id.hex(),
        "byte_count": len(bundle.records[source_id].payload),
        "scalar_count": len(ordered_ids) if accepted else None,
        "unique_scalar_count": len(scalar_ids) if accepted else 0,
        "error": result_value["error"],
        "record_counts": counts,
        "canonical_sha256": hashlib.sha256(bundle.pack()).hexdigest(),
        "learner_ingestion_allowed": False,
    }
    return bundle, report


def build_text(text: str) -> tuple[Bundle, dict]:
    """Strict boundary adapter; invalid surrogates cannot form source bytes."""
    require(type(text) is str, "Text must be exact str")
    # Each scalar needs at least one byte: bound before allocating encoding.
    require(len(text) <= MAX_SOURCE_BYTES, "Text exceeds source length limit")
    try:
        data = text.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        raise ContractError("Text contains a surrogate; no strict UTF-8 source") from None
    return build(data)


def verify_bundle(bundle: Bundle) -> dict:
    """Full replay rejects all extra, missing, or semantically altered records."""
    require(isinstance(bundle, Bundle), "Expected Bundle")
    bundle.validate()
    sources = [
        record
        for record in bundle.records.values()
        if isinstance(record, Object) and kind_of(record) == "source-bytes"
    ]
    require(len(sources) == 1, "Expected exactly one source-bytes Object")
    replay, report = build(sources[0].payload, use_collection=False)
    require(bundle.pack() == replay.pack(), "Bundle differs from full replay")
    return report


def reconstruct(bundle: Bundle) -> bytes:
    """Rebuild from the verified ordered scalar sequence, never saved source."""
    report = verify_bundle(bundle)
    require(report["status"] == "accepted", "Cannot reconstruct rejected import")
    sequence_id = bytes.fromhex(report["sequence_id"])
    sequence = bundle.records[sequence_id]
    require(isinstance(sequence, Object), "Sequence must be Object")
    payload = sequence.payload
    require(len(payload) >= 8, "Truncated sequence count")
    count = int.from_bytes(payload[:8], "big")
    require(count <= MAX_SCALARS, "Sequence count exceeds limit")
    require(len(payload) == 8 + 32 * count, "Sequence payload length mismatch")
    require(count == report["scalar_count"], "Sequence count mismatch")
    chunks = []
    assigned = repertoire()
    for index in range(count):
        start = 8 + 32 * index
        key = payload[start : start + 32]
        record = bundle.records.get(key)
        require(isinstance(record, Object), "Missing scalar Object")
        require(kind_of(record) == "unicode-scalar", "Invalid sequence child")
        require(len(record.payload) == 4, "Invalid scalar payload length")
        cp = int.from_bytes(record.payload, "big")
        require(unicode_objects.scalar_valid(cp), "Invalid scalar value")
        require(cp in assigned, "Unassigned scalar value")
        require(record == _scalar_object(cp), "Noncanonical scalar Object")
        chunks.append(chr(cp).encode("utf-8", errors="strict"))
    reconstructed = b"".join(chunks)
    require(len(reconstructed) <= MAX_SOURCE_BYTES, "Reconstruction exceeds limit")
    source = bundle.records[bytes.fromhex(report["source_id"])]
    require(reconstructed == source.payload, "Reconstruction differs from source")
    return reconstructed
