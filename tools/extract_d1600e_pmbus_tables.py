#!/usr/bin/env python3
"""Extract D1600E 00.3D.67 PMBus dispatch tables from the 4-byte-slot image.

The image is 24-bit little-endian program words stored in 4-byte slots.
PC increments by 2 for each slot. The low 16 bits at each slot are the PSV
data words used by the dispatch tables.
"""
from pathlib import Path
import argparse
import csv

READ_TABLE_PC = 0x14D8
READ_TABLE_COUNT = 85
WRITE_TABLE_PC = 0x18A2
WRITE_TABLE_COUNT = 43

COMMAND_NAMES = {
    0x00: "PAGE",
    0x03: "CLEAR_FAULTS",
    0x05: "PAGE_PLUS_WRITE",
    0x06: "PAGE_PLUS_READ",
    0x19: "CAPABILITY",
    0x1A: "QUERY",
    0x1B: "SMBALERT_MASK",
    0x30: "COEFFICIENTS",
    0x3A: "FAN_CONFIG_1_2",
    0x3B: "FAN_COMMAND_1",
    0x40: "VOUT_OV_FAULT_LIMIT",
    0x44: "VOUT_UV_FAULT_LIMIT",
    0x46: "IOUT_OC_FAULT_LIMIT",
    0x4A: "IOUT_OC_WARN_LIMIT",
    0x5D: "IIN_OC_WARN_LIMIT",
    0x6B: "PIN_OP_WARN_LIMIT",
    0x78: "STATUS_BYTE",
    0x79: "STATUS_WORD",
    0x7A: "STATUS_VOUT",
    0x7B: "STATUS_IOUT",
    0x7C: "STATUS_INPUT",
    0x7D: "STATUS_TEMPERATURE",
    0x7E: "STATUS_CML",
    0x7F: "STATUS_OTHER",
    0x81: "STATUS_FANS_1_2",
    0x86: "READ_EIN",
    0x87: "READ_EOUT",
    0x88: "READ_VIN",
    0x89: "READ_IIN",
    0x8B: "READ_VOUT",
    0x8C: "READ_IOUT",
    0x8D: "READ_TEMPERATURE_1",
    0x8E: "READ_TEMPERATURE_2",
    0x8F: "READ_TEMPERATURE_3",
    0x90: "READ_FAN_SPEED_1",
    0x96: "READ_POUT",
    0x97: "READ_PIN",
    0x98: "PMBUS_REVISION",
    0x99: "MFR_ID",
    0x9A: "MFR_MODEL",
    0x9B: "MFR_REVISION",
    0x9C: "MFR_LOCATION",
    0x9D: "MFR_DATE",
    0x9E: "MFR_SERIAL",
    0x9F: "APP_PROFILE_SUPPORT",
    0xA7: "MFR_POUT_MAX",
    0xB0: "USER_DATA_00",
    0xB1: "USER_DATA_01",
    0xB2: "USER_DATA_02",
    0xB3: "USER_DATA_03",
    0xC0: "MFR_MAX_TEMP_1",
    0xC1: "MFR_MAX_TEMP_2",
    0xC2: "MFR_MAX_TEMP_3",
}


def load_words(path: Path):
    raw = path.read_bytes()
    if len(raw) % 4:
        raise ValueError("Program image size is not divisible by 4")
    return [int.from_bytes(raw[i:i + 3], "little") for i in range(0, len(raw), 4)]


def read_table(words, pc, count, packed_descriptor=False):
    rows = []
    base = pc // 2
    for index in range(count):
        key = words[base + index * 2] & 0xFFFF
        handler = words[base + index * 2 + 1] & 0xFFFF
        if packed_descriptor:
            descriptor = key >> 8
            command = key & 0xFF
        else:
            descriptor = ""
            command = key & 0xFF
        rows.append({
            "index": index,
            "key": f"0x{key:04X}",
            "descriptor": f"0x{descriptor:02X}" if packed_descriptor else "",
            "command": f"0x{command:02X}",
            "name": COMMAND_NAMES.get(command, "MFR_SPECIFIC_OR_UNMAPPED"),
            "handler_pc": f"0x{handler:04X}",
            "handler_present": handler != 0,
        })
    return rows


def write_csv(path: Path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("image", type=Path)
    parser.add_argument("--outdir", type=Path, default=Path("pmbus_tables_out"))
    args = parser.parse_args()

    words = load_words(args.image)
    read_rows = read_table(words, READ_TABLE_PC, READ_TABLE_COUNT, False)
    write_rows = read_table(words, WRITE_TABLE_PC, WRITE_TABLE_COUNT, True)

    write_csv(args.outdir / "read_command_table.csv", read_rows)
    write_csv(args.outdir / "write_command_table.csv", write_rows)

    print(f"Read table: PC 0x{READ_TABLE_PC:04X}, {len(read_rows)} entries")
    print(f"Write table: PC 0x{WRITE_TABLE_PC:04X}, {len(write_rows)} entries")
    print("READ_VOUT:", next(r for r in read_rows if r["command"] == "0x8B"))
    print("READ_IOUT:", next(r for r in read_rows if r["command"] == "0x8C"))
    print("READ_FAN_SPEED_1:", next(r for r in read_rows if r["command"] == "0x90"))
    print("FAN_COMMAND_1:", next(r for r in write_rows if r["command"] == "0x3B"))


if __name__ == "__main__":
    main()
