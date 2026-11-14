#!/usr/bin/env python3
"""Extract the 4-byte dsPIC33 program slots from Dell 00.3D.67 payload."""
from pathlib import Path
import argparse

HEADER_END = 0x144


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", help="extracted 095HR5_190AD_00.3D.67 payload")
    ap.add_argument("-o", "--output", default="D1600E_00.3D.67_dspic_program_4byte_slots.bin")
    args = ap.parse_args()

    blob = Path(args.input).read_bytes()
    if len(blob) <= HEADER_END or (len(blob) - HEADER_END) % 4:
        raise SystemExit("Invalid payload length / 4-byte record alignment")
    fields = blob[:HEADER_END].split(b"\n")[:7]
    if len(fields) < 7 or fields[2] != b"00.3D.67" or fields[4] != b"095HR5A00":
        raise SystemExit("Unexpected firmware header; refusing extraction")

    image = blob[HEADER_END:]
    Path(args.output).write_bytes(image)
    print(f"slots={len(image)//4}, bytes={len(image)}, output={args.output}")


if __name__ == "__main__":
    main()
