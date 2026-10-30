"""Resource-bound regression tests; fixtures contain no learner knowledge."""

from types import SimpleNamespace

import pytest

from tools import unicode_sequences as api
from tools.silicate_contract import ContractError


@pytest.mark.parametrize("maximum", [-1, True, api.MAX_PACK_BYTES + 1, 1.5, None])
def test_read_bounded_validates_budget_before_opening(tmp_path, maximum):
    missing = tmp_path / "nonexistent.bin"
    assert not missing.exists()

    with pytest.raises(ContractError, match="Invalid read byte budget"):
        api.read_bounded(missing, maximum)

    assert not missing.exists()


def test_read_bounded_zero_budget(tmp_path):
    path = tmp_path / "payload.bin"
    path.write_bytes(b"")
    assert api.read_bounded(path, 0) == b""
    assert path.read_bytes() == b""

    path.write_bytes(b"\x00")
    with pytest.raises(ContractError, match="File exceeds byte budget"):
        api.read_bounded(path, 0)
    assert path.read_bytes() == b"\x00"


def test_read_bounded_exact_positive_budget(tmp_path):
    path = tmp_path / "payload.bin"
    budget = 1
    assert budget <= api.MAX_PACK_BYTES

    path.write_bytes(b"\x00")
    assert api.read_bounded(path, budget) == b"\x00"
    assert path.read_bytes() == b"\x00"

    path.write_bytes(b"\x00\x01")
    with pytest.raises(ContractError, match="File exceeds byte budget"):
        api.read_bounded(path, budget)
    assert path.read_bytes() == b"\x00\x01"


def test_load_bounds_enumeration_before_reading_artifacts(tmp_path, monkeypatch):
    directory = tmp_path / "artifacts"
    directory.mkdir()
    allowed_names = sorted(api.REQUIRED | {"README.md"})
    assert len(allowed_names) == 6
    unexpected = "unexpected-artifact"
    assert unexpected not in allowed_names

    class BoundedListing:
        def __init__(self):
            self.visits = 0
            self.closed = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_value, traceback):
            self.closed = True
            return False

        def __iter__(self):
            return self

        def __next__(self):
            if self.visits >= 7:
                raise AssertionError("load requested an eighth directory entry")
            index = self.visits
            self.visits += 1
            name = allowed_names[index] if index < 6 else unexpected
            return SimpleNamespace(name=name)

    listing = BoundedListing()
    scandir_calls = []

    def fake_scandir(path):
        assert path == directory
        scandir_calls.append(path)
        return listing

    monkeypatch.setattr(api.os, "scandir", fake_scandir)

    # No artifact files exist: enumeration must fail before file validation/read.
    with pytest.raises(ContractError, match="Invalid artifact set"):
        api.load(directory)

    assert scandir_calls == [directory]
    assert listing.visits == 7
    assert listing.closed
