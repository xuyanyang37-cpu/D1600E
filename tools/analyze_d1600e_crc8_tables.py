#!/usr/bin/env python3
"""Extract and verify the CRC-8 nibble tables in Dell/Delta D1600E 00.3D.67.

Input program image format: 4-byte slots (24-bit little-endian program word + pad).
PC advances by 2 per slot. The PSV data pointers 0x9882 and 0x9892 map to
program PCs 0x1882 and 0x1892 when PSVPAG=0.
"""
from pathlib import Path
import argparse


def crc8_nibble_tables(poly: int = 0x07):
    low, high = [], []
    for n in range(16):
        c = n
        for _ in range(8):
            c = ((c << 1) ^ poly) & 0xFF if c & 0x80 else (c << 1) & 0xFF
        low.append(c)

        c = n << 4
        for _ in range(8):
            c = ((c << 1) ^ poly) & 0xFF if c & 0x80 else (c << 1) & 0xFF
        high.append(c)
    return bytes(low), bytes(high)


def program_data_bytes(image: bytes, pc: int, slot_count: int) -> bytes:
    """Read low 16-bit data word from consecutive 4-byte program slots."""
    out = bytearray()
    for i in range(slot_count):
        offset = (pc // 2 + i) * 4
        if offset + 2 > len(image):
            raise ValueError(f"PC 0x{pc + i * 2:04X} outside image")
        out.extend(image[offset:offset + 2])
    return bytes(out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "image",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parent
        / "D1600E_00.3D.67_dspic_program_4byte_slots.bin",
    )
    args = parser.parse_args()
    image = args.image.read_bytes()

    low = program_data_bytes(image, 0x1882, 8)
    high = program_data_bytes(image, 0x1892, 8)
    expected_low, expected_high = crc8_nibble_tables(0x07)

    print(f"Image: {args.image}")
    print("Polynomial: 0x07 (CRC-8/SMBus PEC polynomial)")
    print("PSV 0x9882 -> program PC 0x1882 when PSVPAG=0")
    print("Extracted low table :", low.hex(" ").upper())
    print("Expected low table  :", expected_low.hex(" ").upper())
    print("Low table exact match:", low == expected_low)
    print("PSV 0x9892 -> program PC 0x1892 when PSVPAG=0")
    print("Extracted high table:", high.hex(" ").upper())
    print("Expected high table :", expected_high.hex(" ").upper())
    print("High table exact match:", high == expected_high)
    print("Both exact matches  :", low == expected_low and high == expected_high)


if __name__ == "__main__":
    main()
