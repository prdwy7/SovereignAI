"""Check M0.1 golden records and optionally the pinned local Rust source oracle."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

from tools.silicate_contract import FORMAT, decode, encode, identity

ROOT = Path(__file__).resolve().parent.parent


def verify_sources(manifest: dict) -> None:
    for source in (manifest["selected_source"], manifest["alternative_source"]):
        base = Path(source["path"])
        for name, digest in source["files_sha256"].items():
            if hashlib.sha256((base / name).read_bytes()).hexdigest() != digest:
                raise ValueError(f"Pinned source changed: {base / name}")
    selected = manifest["selected_source"]
    revision = subprocess.check_output(
        ["git", "-C", selected["path"], "rev-parse", "HEAD"], text=True
    ).strip()
    if revision != selected["git_revision"]:
        raise ValueError("Selected source revision changed")


def verify(*, source_oracle: bool = False) -> dict:
    fixture = json.loads((ROOT / "fixtures/silicate-v1/golden.json").read_text())
    manifest = json.loads((ROOT / "manifests/silicate-foundation.json").read_text())
    if fixture["format"] != FORMAT or manifest["format"] != FORMAT:
        raise ValueError("Fixture/source format mismatch")
    for vector in fixture["vectors"]:
        wire = bytes.fromhex(vector["canonical_hex"])
        record = decode(vector["kind"], wire, bytes.fromhex(vector["id_hex"]))
        if encode(record) != wire or identity(record).hex() != vector["id_hex"]:
            raise ValueError(f"Fixture mismatch: {vector['name']}")
    if source_oracle:
        verify_sources(manifest)
        lock = ROOT / "probes/silicate-source/Cargo.lock"
        if hashlib.sha256(lock.read_bytes()).hexdigest() != manifest["probe_lock_sha256"]:
            raise ValueError("Rust probe dependency lock changed")
        environment = {**os.environ, "SILICATE_SOURCE_ROOT": manifest["selected_source"]["path"]}
        result = subprocess.run(
            [
                "cargo",
                "run",
                "--locked",
                "--offline",
                "--manifest-path",
                str(ROOT / manifest["probe_manifest"]),
                "--target-dir",
                str(ROOT / ".cache/silicate-probe-target"),
            ],
            env=environment,
            cwd=ROOT,
            check=True,
            text=True,
            capture_output=True,
        )
        expected = [
            "|".join(v[field] for field in ("name", "kind", "canonical_hex", "id_hex"))
            for v in fixture["vectors"]
        ]
        if result.stdout.splitlines() != expected:
            raise ValueError("Local Rust source disagrees with pinned golden vectors")
    return {
        "build": "M0.1",
        "format": FORMAT,
        "vectors_verified": len(fixture["vectors"]),
        "source_oracle_verified": source_oracle,
        "production_kernel_integrated": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-oracle", action="store_true")
    args = parser.parse_args()
    try:
        print(json.dumps(verify(source_oracle=args.source_oracle), indent=2))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(f"Contract verification failed: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
