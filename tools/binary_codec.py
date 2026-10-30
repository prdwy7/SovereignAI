"""Bounded, lossless bit packing and deterministic local prefix codes for M0.3."""

from __future__ import annotations

import heapq
from collections import Counter

from tools.silicate_contract import ContractError

MAX_BITS = 4096
MAX_ENCODED_BITS = MAX_BITS * 64
MAX_PATTERNS = 32


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ContractError(message)


def bits_valid(bits: str, limit: int = MAX_BITS) -> None:
    require(
        isinstance(bits, str) and len(bits) <= limit and set(bits) <= {"0", "1"},
        "Invalid or oversized bit string",
    )


def pack_bits(bits: str, limit: int = MAX_BITS) -> bytes:
    bits_valid(bits, limit)
    padded = bits + "0" * (-len(bits) % 8)
    data = bytes(int(padded[i : i + 8], 2) for i in range(0, len(padded), 8))
    return len(bits).to_bytes(4, "big") + data


class Reader:
    def __init__(self, data: bytes):
        require(isinstance(data, bytes), "Expected bytes")
        self.data, self.position = data, 0

    def take(self, count: int) -> bytes:
        require(
            type(count) is int and 0 <= count <= len(self.data) - self.position,
            "Truncated binary payload",
        )
        start = self.position
        self.position += count
        return self.data[start : self.position]

    def uint(self, size: int) -> int:
        return int.from_bytes(self.take(size), "big")

    def bits(self, limit: int = MAX_BITS) -> str:
        count = self.uint(4)
        require(count <= limit, "Bit length exceeds budget")
        packed = self.take((count + 7) // 8)
        padding = (-count) % 8
        require(not padding or not (packed[-1] & ((1 << padding) - 1)), "Nonzero padding bits")
        return "".join(f"{byte:08b}" for byte in packed)[:count]

    def finish(self) -> None:
        require(self.position == len(self.data), "Trailing binary payload bytes")


def unpack_bits(data: bytes, limit: int = MAX_BITS) -> str:
    reader = Reader(data)
    bits = reader.bits(limit)
    reader.finish()
    return bits


def validate_patterns(patterns: tuple[str, ...]) -> None:
    require(
        isinstance(patterns, tuple) and 2 <= len(patterns) <= MAX_PATTERNS + 2,
        "Invalid pattern dictionary size",
    )
    for pattern in patterns:
        bits_valid(pattern, 16)
        require(bool(pattern), "Empty pattern cannot advance decoding")
    require(
        len(set(patterns)) == len(patterns) and {"0", "1"} <= set(patterns),
        "Dictionary must include unique zero and one fallbacks",
    )


def segment(bits: str, patterns: tuple[str, ...]) -> tuple[tuple[str, ...], int]:
    bits_valid(bits)
    validate_patterns(patterns)
    choices = sorted(patterns, key=lambda p: (-len(p), p))
    position, comparisons = 0, 0
    output = []
    while position < len(bits):
        for pattern in choices:
            comparisons += 1
            if bits.startswith(pattern, position):
                output.append(pattern)
                position += len(pattern)
                break
    return tuple(output), comparisons


def prefix_codes(counts: Counter) -> dict[str, str]:
    patterns = tuple(sorted(counts))
    validate_patterns(patterns)
    heap = []
    for pattern in patterns:
        count = counts[pattern]
        require(type(count) is int and count >= 0, "Invalid symbol frequency")
        heapq.heappush(heap, (max(1, count), pattern, pattern))
    while len(heap) > 1:
        left, right = heapq.heappop(heap), heapq.heappop(heap)
        heapq.heappush(heap, (left[0] + right[0], min(left[1], right[1]), (left[2], right[2])))
    codes = {}

    def visit(node, prefix):
        if isinstance(node, str):
            codes[node] = prefix
        else:
            visit(node[0], prefix + "0")
            visit(node[1], prefix + "1")

    visit(heap[0][2], "")
    validate_codes(codes)
    return codes


def validate_codes(codes: dict[str, str]) -> None:
    require(isinstance(codes, dict), "Expected codebook mapping")
    validate_patterns(tuple(codes))
    for code in codes.values():
        bits_valid(code, 64)
        require(bool(code), "Empty prefix code")
    ordered = sorted(codes.values())
    require(
        all(not b.startswith(a) for a, b in zip(ordered, ordered[1:], strict=False)),
        "Duplicate or non-prefix-free codebook",
    )


def encode_tokens(tokens: tuple[str, ...], codes: dict[str, str]) -> str:
    validate_codes(codes)
    require(
        len(tokens) <= MAX_BITS and all(token in codes for token in tokens),
        "Unknown token or token budget exceeded",
    )
    result = "".join(codes[token] for token in tokens)
    bits_valid(result, MAX_ENCODED_BITS)
    return result


def decode_tokens(
    encoded: str, codes: dict[str, str], expected_bits: int, expected_tokens: int
) -> tuple[str, int]:
    validate_codes(codes)
    bits_valid(encoded, MAX_ENCODED_BITS)
    require(
        type(expected_bits) is int and 0 <= expected_bits <= MAX_BITS, "Invalid reconstruction size"
    )
    require(
        type(expected_tokens) is int and 0 <= expected_tokens <= MAX_BITS, "Invalid token count"
    )
    reverse = {code: pattern for pattern, code in codes.items()}
    prefixes = {code[:i] for code in reverse for i in range(1, len(code))}
    partial, output, length = "", [], 0
    for bit in encoded:
        partial += bit
        if partial in reverse:
            token = reverse[partial]
            output.append(token)
            length += len(token)
            require(
                length <= expected_bits and len(output) <= expected_tokens,
                "Decoded output exceeds declared size",
            )
            partial = ""
        else:
            require(partial in prefixes, "Unknown encoded prefix")
    require(
        not partial and length == expected_bits and len(output) == expected_tokens,
        "Truncated stream or reconstruction count mismatch",
    )
    return "".join(output), len(encoded)
