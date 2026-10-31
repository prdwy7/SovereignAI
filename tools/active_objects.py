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
"""M0.2 bounded active-object prototype. No learner, language model or sentience test."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from functools import cache
from pathlib import Path

from tools import unicode_objects as unicode
from tools.silicate_contract import (
    FORMAT,
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
DEFAULT_DIRECTORY = ROOT / "data/experiments/active-objects/m0-2"
PROFILE = "sovereign-active-objects-v1"
FIELDS = {
    "registry": {"profile", "maps"},
    "run": {"name", "max_commands", "unicode_pack_sha256", "learner_ingestion_allowed"},
    "operation": {"name", "version"},
    "rule": {"operation", "version", "scope"},
    "instance": {"name", "run", "level", "symbol", "members", "max_steps", "memory_limit"},
    "state": {"instance", "previous", "observation", "observations", "matches", "memory"},
    "observation": {"instance", "event", "source", "symbol", "root", "origin", "policy"},
    "result": {"instance", "observation", "matched", "mode"},
    "policy": {"group", "member", "operation", "automatic"},
    "receipt-reference": {"kind", "id"},
    "command": {"run", "ordinal", "previous", "action", "arguments"},
    "relation-type": {"name"},
}
ACTIONS = ("atom", "group", "allow_forward", "observe", "forward")
LINKS = ("member", "symbol", "state-of", "supersedes", "observes", "derived-from")
SCHEMA_SQL = """
CREATE TABLE records (
    id BLOB PRIMARY KEY CHECK(length(id)=32),
    kind TEXT NOT NULL CHECK(kind IN ('object','relation','derivation')),
    wire BLOB NOT NULL
);
CREATE TABLE metadata (key TEXT PRIMARY KEY, value BLOB NOT NULL);
CREATE TABLE commands (ordinal INTEGER PRIMARY KEY, command BLOB UNIQUE, receipt BLOB UNIQUE);
CREATE TABLE instances (name TEXT PRIMARY KEY, id BLOB UNIQUE, state BLOB NOT NULL);
CREATE TABLE requests (key TEXT PRIMARY KEY, arguments BLOB NOT NULL, receipt BLOB NOT NULL);
"""


def canonical(value: dict) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False
    ).encode()


def check(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def hex_id(value: str) -> bytes:
    check(
        isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None,
        "Expected a canonical 32-byte hexadecimal identity",
    )
    return bytes.fromhex(value)


def label(value: str) -> str:
    check(
        isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,120}", value) is not None,
        "Labels must contain 1..120 ASCII letters, digits or _ . : -",
    )
    return value


def bounded(value: int, maximum: int, name: str) -> int:
    check(type(value) is int and 1 <= value <= maximum, f"Invalid {name} budget")
    return value


@cache
def handle(role: str, kind: str) -> bytes:
    return hashlib.sha256(f"{PROFILE}:{role}:{kind}".encode()).digest()


def obj(kind: str, payload: dict) -> Object:
    check(
        kind in FIELDS and isinstance(payload, dict) and set(payload) == FIELDS[kind],
        "Invalid active Object fields",
    )
    return Object(
        *(handle(role, kind) for role in ("type", "definition", "schema")), canonical(payload)
    )


def unpack(record: Object, expected: str | None = None) -> tuple[str, dict]:
    check(isinstance(record, Object), "Expected an Object")
    for kind in FIELDS:
        if record.object_type != handle("type", kind):
            continue
        check(expected is None or kind == expected, "Unexpected Object type")
        try:
            value = json.loads(record.payload)
        except (ValueError, UnicodeError):
            raise ContractError("Invalid Object JSON") from None
        check(obj(kind, value) == record, "Invalid binding or noncanonical payload")
        return kind, value
    raise ContractError("Unknown active Object type")


def bootstrap() -> tuple[dict, tuple[Object, ...]]:
    maps = {role: dict(values) for role, values in unicode.EXPECTED_REGISTRY["maps"].items()}
    declarations = list(unicode.DECLARATION_RECORDS)
    for kind in sorted(FIELDS):
        for role in ("type", "definition", "schema"):
            payload = {
                "role": role,
                "name": kind,
                "handle": handle(role, kind).hex(),
                "spec": {
                    "profile": PROFILE,
                    "validator": "active_objects.py:v1",
                    "fields": sorted(FIELDS[kind]),
                    "purpose": "engineering-only",
                },
            }
            declaration = Object(
                *(unicode.handle(r, "declaration") for r in ("type", "definition", "schema")),
                canonical(payload),
            )
            maps[role][handle(role, kind).hex()] = identity(declaration).hex()
            declarations.append(declaration)
    return maps, tuple(declarations)


REGISTRY_MAPS, DECLARATIONS = bootstrap()
REGISTRY = obj("registry", {"profile": PROFILE, "maps": REGISTRY_MAPS})
OPERATIONS = {name: obj("operation", {"name": name, "version": 1}) for name in ACTIONS}
RULES = {
    name: obj(
        "rule",
        {
            "operation": identity(operation).hex(),
            "version": 1,
            "scope": "explicit-group-to-member" if name == "forward" else "local",
        },
    )
    for name, operation in OPERATIONS.items()
}
RELATION_TYPES = {name: obj("relation-type", {"name": name}) for name in LINKS}
BOOTSTRAP_RECORDS = (
    *DECLARATIONS,
    REGISTRY,
    *OPERATIONS.values(),
    *RULES.values(),
    *RELATION_TYPES.values(),
)


def validate_object(record: Object) -> None:
    for role, value in zip(
        ("type", "definition", "schema"),
        (record.object_type, record.definition, record.schema),
        strict=True,
    ):
        check(value.hex() in REGISTRY_MAPS[role], "Unresolved declaration")
    if record in DECLARATIONS:
        return
    if record.object_type == unicode.handle("type", "unicode-scalar"):
        unicode.validate_object(record, unicode.EXPECTED_REGISTRY)
        return
    unpack(record)


def ref(record: Record) -> Reference:
    return Reference(family(record), identity(record))


def edge(source: Object, name: str, target: Object, ordering: int | None = None) -> Relation:
    return Relation(
        identity(source), identity(RELATION_TYPES[name]), identity(target), ordering, b""
    )


def source_symbol(scalar: int) -> Object:
    value = unicode.inspect(unicode.DEFAULT_DESTINATION, scalar)
    record = Object(
        *(bytes.fromhex(value[k]) for k in ("type", "definition", "schema")),
        bytes.fromhex(value["payload_hex"]),
    )
    check(identity(record).hex() == value["id"], "Unicode identity mismatch")
    return record


class Store:
    """SQLite is the physical container; only three canonical record families are stored.

    commands/instances/requests are rebuildable indexes. metadata pins the genesis run.
    The instance-level word 'scope' describes interaction history, not consciousness.
    """

    def __init__(self, connection: sqlite3.Connection):
        self.db = connection
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA synchronous=FULL")
        self.failpoint = None  # Engineering fault-injection hook; never a learned operation.

    @classmethod
    def create(cls, path: Path | None, name: str, max_commands: int = 1024) -> Store:
        label(name)
        bounded(max_commands, 4096, "command")
        if path is not None:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("xb"):
                pass
        connection = sqlite3.connect(":memory:" if path is None else path, isolation_level=None)
        store = cls(connection)
        store.db.executescript(SCHEMA_SQL)
        pack = json.loads((unicode.DEFAULT_DESTINATION / "manifest.json").read_text())[
            "file_sha256"
        ]["objects.bin"]
        run = obj(
            "run",
            {
                "name": name,
                "max_commands": max_commands,
                "unicode_pack_sha256": pack,
                "learner_ingestion_allowed": False,
            },
        )
        with store.transaction():
            for record in (*BOOTSTRAP_RECORDS, run):
                store.put(record)
            store.db.execute("INSERT INTO metadata VALUES ('run', ?)", (identity(run),))
        return store

    @classmethod
    def open(cls, path: Path) -> Store:
        check(path.is_file(), "Active store does not exist")
        store = cls(
            sqlite3.connect(path.resolve().as_uri() + "?mode=rw", uri=True, isolation_level=None)
        )
        try:
            store.verify()
        except BaseException:
            store.close()
            raise
        return store

    def close(self) -> None:
        self.db.close()

    @contextmanager
    def transaction(self):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            yield
            self.db.execute("COMMIT")
        except BaseException:
            if self.db.in_transaction:
                try:
                    self.db.execute("ROLLBACK")
                except sqlite3.Error:
                    pass  # Preserve the initiating exception if the connection has failed.
            raise

    def put(self, record: Record) -> bytes:
        if isinstance(record, Object):
            validate_object(record)
        rid, kind, wire = identity(record), family(record), encode(record)
        existing = self.db.execute("SELECT kind,wire FROM records WHERE id=?", (rid,)).fetchone()
        check(existing is None or existing == (kind, wire), "Record identity collision")
        self.db.execute("INSERT OR IGNORE INTO records VALUES (?,?,?)", (rid, kind, wire))
        return rid

    def get(self, rid: bytes) -> Record:
        row = self.db.execute("SELECT kind,wire FROM records WHERE id=?", (rid,)).fetchone()
        check(row is not None, "Missing record reference")
        return decode(row[0], row[1], rid)

    def data(self, rid: bytes, kind: str) -> dict:
        return unpack(self.get(rid), kind)[1]

    def run(self) -> Object:
        row = self.db.execute("SELECT value FROM metadata WHERE key='run'").fetchone()
        check(row is not None, "Missing genesis run")
        record = self.get(row[0])
        unpack(record, "run")
        return record

    def instance(self, rid: bytes) -> tuple[Object, Object]:
        row = self.db.execute("SELECT state FROM instances WHERE id=?", (rid,)).fetchone()
        check(row is not None, "Unknown active instance")
        instance, state = self.get(rid), self.get(row[0])
        unpack(instance, "instance")
        check(unpack(state, "state")[1]["instance"] == rid.hex(), "State scope mismatch")
        return instance, state

    def inspect(self, name: str) -> dict:
        row = self.db.execute("SELECT id,state FROM instances WHERE name=?", (name,)).fetchone()
        check(row is not None, "Unknown instance name")
        return {
            "id": row[0].hex(),
            "state_id": row[1].hex(),
            "instance": self.data(row[0], "instance"),
            "state": self.data(row[1], "state"),
            "subjective_experience": "not_established",
        }

    def _request_key(self, action: str, args: dict) -> str:
        if action in ("atom", "group"):
            return "instance:" + label(args["name"])
        if action == "allow_forward":
            return "policy:" + hex_id(args["group"]).hex() + ":" + hex_id(args["member"]).hex()
        if action == "observe":
            return "event:" + hex_id(args["instance"]).hex() + ":" + label(args["event"])
        policy = self.data(hex_id(args["policy"]), "policy")
        observation = self._source_observation(hex_id(args["receipt"]))
        return "forward:" + policy["member"] + ":" + unpack(observation, "observation")[1]["root"]

    def submit(self, action: str, **args) -> str:
        """One explicit command per transaction, with idempotency and no recursive dispatch."""
        check(action in ACTIONS, "Unsupported operation")
        expected = {
            "atom": {"name", "scalar", "max_steps", "memory_limit"},
            "group": {"name", "members", "max_steps", "memory_limit"},
            "allow_forward": {"group", "member"},
            "observe": {"instance", "event", "source", "scalar"},
            "forward": {"policy", "receipt"},
        }
        check(set(args) == expected[action], "Invalid command arguments")
        arguments = canonical({"action": action, "arguments": args})
        with self.transaction():
            key = self._request_key(action, args)
            old = self.db.execute(
                "SELECT arguments,receipt FROM requests WHERE key=?", (key,)
            ).fetchone()
            if old is not None:
                check(old[0] == arguments, "Idempotency key reused with different content")
                return old[1].hex()
            previous = self.db.execute(
                "SELECT ordinal,command FROM commands ORDER BY ordinal DESC LIMIT 1"
            ).fetchone()
            ordinal = previous[0] + 1 if previous else 1
            run = self.run()
            check(ordinal <= unpack(run, "run")[1]["max_commands"], "Command budget exhausted")
            command = obj(
                "command",
                {
                    "run": identity(run).hex(),
                    "ordinal": ordinal,
                    "previous": previous[1].hex() if previous else None,
                    "action": action,
                    "arguments": args,
                },
            )
            self.put(command)
            inputs, outputs = self._execute(action, args)
            receipt = Derivation(
                "deterministic",
                tuple(ref(r) for r in (command, run, RULES[action], *inputs)),
                identity(OPERATIONS[action]),
                identity(RULES[action]),
                1,
                canonical({"profile": PROFILE}),
                tuple(ref(r) for r in outputs),
            )
            for record in outputs:
                self.put(record)
            self.put(receipt)
            self.db.execute(
                "INSERT INTO commands VALUES (?,?,?)",
                (ordinal, identity(command), identity(receipt)),
            )
            self.db.execute(
                "INSERT INTO requests VALUES (?,?,?)", (key, arguments, identity(receipt))
            )
            if self.failpoint is not None:
                self.failpoint("before_commit")
            result = identity(receipt).hex()
        if self.failpoint is not None:
            self.failpoint("after_commit")
        return result

    def _execute(self, action: str, args: dict) -> tuple[list[Record], list[Record]]:
        if action in ("atom", "group"):
            return self._create_instance(action, args)
        if action == "allow_forward":
            group, _ = self.instance(hex_id(args["group"]))
            member, _ = self.instance(hex_id(args["member"]))
            g, m = unpack(group, "instance")[1], unpack(member, "instance")[1]
            check(
                g["level"] == "group" and m["level"] == "atom" and args["member"] in g["members"],
                "Transfer requires a group and its direct atomic member",
            )
            policy = obj(
                "policy",
                {
                    "group": args["group"],
                    "member": args["member"],
                    "operation": identity(OPERATIONS["forward"]).hex(),
                    "automatic": False,
                },
            )
            return [group, member], [policy]
        if action == "observe":
            label(args["source"])
            instance, state = self.instance(hex_id(args["instance"]))
            symbol = source_symbol(args["scalar"])
            self.put(symbol)
            observation = obj(
                "observation",
                {
                    "instance": args["instance"],
                    "event": label(args["event"]),
                    "source": args["source"],
                    "symbol": identity(symbol).hex(),
                    "root": hashlib.sha256(
                        canonical(
                            {
                                "instance": args["instance"],
                                "event": args["event"],
                                "source": args["source"],
                            }
                        )
                    ).hexdigest(),
                    "origin": None,
                    "policy": None,
                },
            )
            return self._transition(instance, state, observation, symbol, [], [])
        policy = self.get(hex_id(args["policy"]))
        p = unpack(policy, "policy")[1]
        check(
            p["automatic"] is False and p["operation"] == identity(OPERATIONS["forward"]).hex(),
            "Unsupported transfer policy",
        )
        source = self._source_observation(hex_id(args["receipt"]))
        value = unpack(source, "observation")[1]
        check(value["instance"] == p["group"], "Transfer source outside policy scope")
        group, _ = self.instance(hex_id(p["group"]))
        check(
            p["member"] in unpack(group, "instance")[1]["members"], "Transfer target outside group"
        )
        instance, state = self.instance(hex_id(p["member"]))
        check(
            unpack(instance, "instance")[1]["level"] == "atom", "Only atomic targets are supported"
        )
        symbol = self.get(hex_id(value["symbol"]))
        receipt_ref = obj("receipt-reference", {"kind": "derivation", "id": args["receipt"]})
        observation = obj(
            "observation",
            {
                "instance": p["member"],
                "event": "forward:" + identity(source).hex(),
                "source": "explicit-group-transfer",
                "symbol": value["symbol"],
                "root": value["root"],
                "origin": identity(source).hex(),
                "policy": identity(policy).hex(),
            },
        )
        return self._transition(
            instance,
            state,
            observation,
            symbol,
            [policy, group, source, receipt_ref],
            [receipt_ref, edge(observation, "derived-from", source)],
        )

    def _create_instance(self, action: str, args: dict) -> tuple[list[Record], list[Record]]:
        check(
            self.db.execute("SELECT count(*) FROM instances").fetchone()[0] < 64,
            "Instance budget exhausted",
        )
        max_steps = bounded(args["max_steps"], 4096, "step")
        memory_limit = bounded(args["memory_limit"], 256, "memory")
        members, symbol, inputs = [], None, []
        if action == "atom":
            atom = source_symbol(args["scalar"])
            self.put(atom)
            symbol = identity(atom).hex()
            inputs.append(atom)
        else:
            members = args["members"]
            check(
                isinstance(members, list) and 2 <= len(members) <= 64,
                "Group requires 2..64 members",
            )
            check(len(set(members)) == len(members), "Duplicate group member")
            for member in members:
                item, _ = self.instance(hex_id(member))
                check(
                    unpack(item, "instance")[1]["level"] == "atom",
                    "Only flat groups of atoms are supported",
                )
                inputs.append(item)
        instance = obj(
            "instance",
            {
                "name": label(args["name"]),
                "run": identity(self.run()).hex(),
                "level": action,
                "symbol": symbol,
                "members": members,
                "max_steps": max_steps,
                "memory_limit": memory_limit,
            },
        )
        state = obj(
            "state",
            {
                "instance": identity(instance).hex(),
                "previous": None,
                "observation": None,
                "observations": 0,
                "matches": 0,
                "memory": [],
            },
        )
        outputs = [instance, state, edge(state, "state-of", instance)]
        if action == "atom":
            outputs.append(edge(instance, "symbol", inputs[0]))
        else:
            outputs.extend(
                edge(instance, "member", member, index) for index, member in enumerate(inputs)
            )
        self.db.execute(
            "INSERT INTO instances VALUES (?,?,?)",
            (args["name"], identity(instance), identity(state)),
        )
        return inputs, outputs

    def _source_observation(self, rid: bytes) -> Object:
        receipt = self.get(rid)
        check(
            isinstance(receipt, Derivation) and receipt.rule == identity(RULES["observe"]),
            "Transfer requires a committed direct observation receipt",
        )
        check(
            self.db.execute("SELECT 1 FROM commands WHERE receipt=?", (rid,)).fetchone()
            is not None,
            "Uncommitted source receipt",
        )
        observations = [
            self.get(r.identity)
            for r in receipt.outputs
            if r.kind == "object"
            and self.get(r.identity).object_type == handle("type", "observation")
        ]
        check(len(observations) == 1, "Invalid source receipt observation")
        return observations[0]

    def _transition(self, instance, old_state, observation, symbol, extra_inputs, extra_outputs):
        p, s = unpack(instance, "instance")[1], unpack(old_state, "state")[1]
        check(s["observations"] < p["max_steps"], "Step budget exhausted")
        check(len(s["memory"]) < p["memory_limit"], "Memory budget exhausted")
        inputs = [instance, old_state, symbol, *extra_inputs]
        symbols = [p["symbol"]]
        if p["level"] == "group":
            members = [self.get(hex_id(member)) for member in p["members"]]
            inputs.extend(members)
            symbols = [unpack(member, "instance")[1]["symbol"] for member in members]
        matched = identity(symbol).hex() in symbols
        state = obj(
            "state",
            {
                "instance": identity(instance).hex(),
                "previous": identity(old_state).hex(),
                "observation": identity(observation).hex(),
                "observations": s["observations"] + 1,
                "matches": s["matches"] + int(matched),
                "memory": [*s["memory"], identity(observation).hex()],
            },
        )
        result = obj(
            "result",
            {
                "instance": identity(instance).hex(),
                "observation": identity(observation).hex(),
                "matched": matched,
                "mode": "forwarded"
                if unpack(observation, "observation")[1]["policy"]
                else "direct",
            },
        )
        outputs = [
            *extra_outputs,
            observation,
            state,
            result,
            edge(state, "state-of", instance),
            edge(state, "supersedes", old_state),
            edge(observation, "observes", symbol),
        ]
        self.db.execute(
            "UPDATE instances SET state=? WHERE id=?", (identity(state), identity(instance))
        )
        return inputs, outputs

    def output(self, receipt_id: str, kind: str) -> dict:
        receipt = self.get(hex_id(receipt_id))
        check(isinstance(receipt, Derivation), "Expected a Derivation")
        found = [
            r
            for reference in receipt.outputs
            if reference.kind == "object"
            and (r := self.get(reference.identity)).object_type == handle("type", kind)
        ]
        check(len(found) == 1, "Expected exactly one output of the requested type")
        return {"id": identity(found[0]).hex(), **unpack(found[0], kind)[1]}

    def inspect_record(self, record_id: str) -> dict:
        record = self.get(hex_id(record_id))

        def display(value):
            if isinstance(value, bytes):
                return value.hex()
            if isinstance(value, dict):
                return {key: display(item) for key, item in value.items()}
            if isinstance(value, (tuple, list)):
                return [display(item) for item in value]
            return value

        result = {"id": record_id, "kind": family(record), "fields": display(asdict(record))}
        if isinstance(record, Object):
            result["declarations"] = {
                role: REGISTRY_MAPS[role][key.hex()]
                for role, key in zip(
                    ("type", "definition", "schema"),
                    (record.object_type, record.definition, record.schema),
                    strict=True,
                )
            }
            try:
                result["decoded_payload"] = json.loads(record.payload)
            except (ValueError, UnicodeError):
                pass  # Unicode scalar payloads are fixed-width binary, shown above as hex.
        return result

    def snapshot(self) -> dict:
        digest = hashlib.sha256()
        counts = dict.fromkeys(PRIMITIVE_KINDS, 0)
        for rid, kind, wire in self.db.execute("SELECT id,kind,wire FROM records ORDER BY id"):
            digest.update(kind.encode() + rid + len(wire).to_bytes(8, "big") + wire)
            counts[kind] += 1
        return {
            "canonical_sha256": digest.hexdigest(),
            "counts": counts,
            "commands": self.db.execute("SELECT count(*) FROM commands").fetchone()[0],
        }

    def verify(self) -> dict:
        """Re-execute canonical commands, then compare ALL records and derived indexes.

        This verifies the declared executable contract, not scientific truth or learning.
        Direct transition tests separately check expected results and scope boundaries.
        """
        with self.transaction():
            return self._verify_snapshot()

    def _verify_snapshot(self) -> dict:
        check(
            self.db.execute("PRAGMA integrity_check").fetchone()[0] == "ok",
            "SQLite integrity failure",
        )
        commands = []
        for rid, kind, wire in self.db.execute("SELECT id,kind,wire FROM records"):
            record = decode(kind, wire, rid)
            if isinstance(record, Object):
                validate_object(record)
                if record.object_type == handle("type", "command"):
                    commands.append(unpack(record, "command")[1])
            elif isinstance(record, Relation):
                check(
                    isinstance(self.get(record.source), Object)
                    and isinstance(self.get(record.target), Object),
                    "Relation endpoint must be an Object",
                )
                self.data(record.relation_type, "relation-type")
            else:
                check(
                    record.execution_class == "deterministic" and record.rule_version == 1,
                    "Unsupported receipt contract",
                )
                self.data(record.operation, "operation")
                self.data(record.rule, "rule")
                for reference in (*record.inputs, *record.outputs):
                    check(
                        family(self.get(reference.identity)) == reference.kind,
                        "Reference family mismatch",
                    )
        run = unpack(self.run(), "run")[1]
        check(
            run["learner_ingestion_allowed"] is False, "Engineering run cannot supply learner data"
        )
        replica = Store.create(None, run["name"], run["max_commands"])
        try:
            check(replica.run() == self.run(), "Genesis or Unicode source pin mismatch")
            previous = None
            for ordinal, command in enumerate(sorted(commands, key=lambda c: c["ordinal"]), 1):
                check(
                    type(command["ordinal"]) is int
                    and command["ordinal"] == ordinal
                    and command["previous"] == previous
                    and command["run"] == identity(self.run()).hex(),
                    "Broken canonical command chain",
                )
                replica.submit(command["action"], **command["arguments"])
                previous = identity(obj("command", command)).hex()
            check(self.snapshot() == replica.snapshot(), "Replay record mismatch")
            for table, order in (
                ("commands", "ordinal"),
                ("instances", "name"),
                ("requests", "key"),
                ("metadata", "key"),
            ):
                query = f"SELECT * FROM {table} ORDER BY {order}"  # Fixed table names only.
                check(
                    self.db.execute(query).fetchall() == replica.db.execute(query).fetchall(),
                    f"Replay index mismatch: {table}",
                )
            return {
                "verified": True,
                "profile": PROFILE,
                "format": FORMAT,
                **self.snapshot(),
                "replayed_commands": len(commands),
                "learner_ingestion_allowed": False,
                "subjective_experience": "not_established",
            }
        finally:
            replica.close()


def demo(directory: Path) -> dict:
    check(not directory.exists(), "Demo directory already exists; choose a new destination")
    directory.mkdir(parents=True)
    path = directory / "records.sqlite"
    store = Store.create(path, "m0-2-scoped-interaction")
    try:
        for name, scalar in (("atom-a", 0x41), ("atom-b", 0x42)):
            store.submit("atom", name=name, scalar=scalar, max_steps=16, memory_limit=16)
        a, b = store.inspect("atom-a")["id"], store.inspect("atom-b")["id"]
        for index, scalar in enumerate((0x41, 0x42, 0x41), 1):
            store.submit(
                "observe",
                instance=a,
                event=f"atom-{index}",
                source="engineering-demo",
                scalar=scalar,
            )
        before_group = store.inspect("atom-a")
        store.submit("group", name="group-ab", members=[a, b], max_steps=16, memory_limit=16)
        group = store.inspect("group-ab")["id"]
        initial_group = store.inspect("group-ab")
        group_event = store.submit(
            "observe", instance=group, event="group-1", source="engineering-demo", scalar=0x41
        )
        store.submit(
            "observe", instance=group, event="group-2", source="engineering-demo", scalar=0x43
        )
        isolated = store.inspect("atom-a")
        policy_receipt = store.submit("allow_forward", group=group, member=a)
        policy = store.output(policy_receipt, "policy")["id"]
        forwarded = store.submit("forward", policy=policy, receipt=group_event)
        check(
            store.submit("forward", policy=policy, receipt=group_event) == forwarded,
            "Duplicate forwarding changed receipt",
        )
        result = {
            "build": "M0.2",
            "learner_ingestion_allowed": False,
            "subjective_experience": "not_established",
            "atom_before_group": before_group,
            "initial_group": initial_group,
            "atom_after_group_events": isolated,
            "atom_after_explicit_transfer": store.inspect("atom-a"),
            "unaffected_member": store.inspect("atom-b"),
            "group_after_events": store.inspect("group-ab"),
            "group_receipt": group_event,
            "transfer_policy": policy,
            "transfer_receipt": forwarded,
            "scope_isolation": before_group["state_id"] == isolated["state_id"],
        }
        result["verification"] = store.verify()
    finally:
        store.close()
    reopened = Store.open(path)
    try:
        result["restart_state_matches"] = (
            reopened.inspect("atom-a") == result["atom_after_explicit_transfer"]
        )
    finally:
        reopened.close()
    (directory / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("demo", "verify", "inspect", "record", "apply"))
    parser.add_argument("--directory", type=Path, default=DEFAULT_DIRECTORY)
    parser.add_argument("--name", help="Instance name for inspection")
    parser.add_argument("--id", help="Canonical record identity for record inspection")
    parser.add_argument("--request", type=Path, help="Explicit engineering command JSON for apply")
    args = parser.parse_args()
    try:
        if args.command == "demo":
            result = demo(args.directory)
        else:
            store = Store.open(args.directory / "records.sqlite")
            try:
                if args.command == "verify":
                    result = store.verify()
                elif args.command == "inspect":
                    check(args.name is not None, "inspect requires --name")
                    result = store.inspect(args.name)
                elif args.command == "record":
                    check(args.id is not None, "record requires --id")
                    result = store.inspect_record(args.id)
                else:
                    check(args.request is not None, "apply requires --request")
                    request = json.loads(args.request.read_text())
                    check(
                        isinstance(request, dict) and set(request) == {"action", "arguments"},
                        "Invalid request envelope",
                    )
                    receipt = store.submit(request["action"], **request["arguments"])
                    result = {"receipt": receipt, "verification": store.verify()}
            finally:
                store.close()
        print(json.dumps(result, indent=2))
        return 0
    except (ContractError, OSError, ValueError, TypeError, KeyError, sqlite3.Error) as exc:
        print(f"Active Object operation failed: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
