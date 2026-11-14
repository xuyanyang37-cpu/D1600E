#!/usr/bin/env python3
"""Extract candidate 24-bit words from a Dell 95HR5 payload.

This is a format-inspection helper, NOT a dsPIC instruction disassembler.
It preserves the original payload and labels the PC mapping as a candidate.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
from pathlib import Path

DEFAULT_OFFSET = 0x144


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("payload", type=Path, help="Original 86,340-byte payload")
    ap.add_argument("--offset", type=lambda x: int(x, 0), default=DEFAULT_OFFSET)
    ap.add_argument("--csv", type=Path, default=Path("instruction_words.csv"))
    ap.add_argument("--summary", type=Path, default=Path("word_summary.json"))
    args = ap.parse_args()

    data = args.payload.read_bytes()
    if args.offset > len(data):
        ap.error("offset is beyond end of payload")
    body = data[args.offset:]
    if len(body) % 4:
        ap.error(f"payload tail length {len(body)} is not divisible by 4")

    counts: collections.Counter[str] = collections.Counter()
    records = []
    non_ff = []
    run_start = None
    run_end = None

    for i in range(0, len(body), 4):
        b0, b1, b2, pad = body[i:i + 4]
        word = b0 | (b1 << 8) | (b2 << 16)
        word_s = f"0x{word:06X}"
        index = i // 4
        file_off = args.offset + i
        counts[word_s] += 1
        records.append((index, index * 2, file_off, word_s, pad))

        if word != 0xFFFFFF:
            if run_start is None:
                run_start = index
            run_end = index
        elif run_start is not None:
            non_ff.append([run_start, run_end])
            run_start = run_end = None

    if run_start is not None:
        non_ff.append([run_start, run_end])

    with args.csv.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow([
            "word_index", "program_counter_candidate_hex",
            "file_offset_hex", "raw_24bit_word", "padding_byte"
        ])
        for index, pc, off, word_s, pad in records:
            w.writerow([index, f"0x{pc:06X}", f"0x{off:06X}",
                        word_s, f"0x{pad:02X}"])

    summary = {
        "input": str(args.payload),
        "size_bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "md5": hashlib.md5(data).hexdigest(),
        "record_start_offset": args.offset,
        "record_count": len(records),
        "record_stride_bytes": 4,
        "word_encoding_candidate": "little-endian 24-bit in bytes 0..2; byte 3 retained as padding",
        "pc_mapping_candidate": "word_index * 2; must be validated against dsPIC33FJ64GS606",
        "padding_byte_counts": dict(collections.Counter(f"0x{x[4]:02X}" for x in records)),
        "most_common_words": counts.most_common(40),
        "non_0xFFFFFF_runs_by_record_index": non_ff,
        "warning": "No instruction decoding, control-flow recovery, or MCU-image attribution is performed."
    }
    args.summary.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
