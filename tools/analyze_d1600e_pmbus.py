#!/usr/bin/env python3
"""Analyze Dell 095HR5 00.3D.67 payload: PMBus command table and SMBus PEC tables."""
from pathlib import Path
import argparse
import csv

HEADER_END = 0x144
RECORD_SIZE = 4
CMD_TABLE_START = 0x14D8
CMD_TABLE_END = 0x162A  # inclusive handler word
CRC_LOW_PSV = 0x9882
CRC_HIGH_PSV = 0x9892

NAMES = {
    0x00: "PAGE", 0x06: "PAGE_PLUS_READ", 0x19: "CAPABILITY",
    0x1A: "QUERY", 0x1B: "SMBALERT_MASK", 0x30: "COEFFICIENTS",
    0x3A: "FAN_CONFIG_12", 0x3B: "FAN_COMMAND_1",
    0x40: "VOUT_OV_FAULT_LIMIT", 0x44: "VOUT_UV_FAULT_LIMIT",
    0x46: "IOUT_OC_FAULT_LIMIT", 0x4A: "IOUT_OC_WARN_LIMIT",
    0x5D: "IIN_OC_WARN_LIMIT", 0x6B: "PIN_OP_WARN_LIMIT",
    0x78: "STATUS_BYTE", 0x79: "STATUS_WORD", 0x7A: "STATUS_VOUT",
    0x7B: "STATUS_IOUT", 0x7C: "STATUS_INPUT",
    0x7D: "STATUS_TEMPERATURE", 0x7E: "STATUS_CML",
    0x7F: "STATUS_OTHER", 0x81: "STATUS_FAN_12",
    0x88: "READ_VIN", 0x89: "READ_IIN", 0x8B: "READ_VOUT",
    0x8C: "READ_IOUT", 0x8D: "READ_TEMPERATURE_1",
    0x8E: "READ_TEMPERATURE_2", 0x8F: "READ_TEMPERATURE_3",
    0x90: "READ_FAN_SPEED_1", 0x96: "READ_POUT", 0x97: "READ_PIN",
    0x98: "PMBUS_REVISION", 0x99: "MFR_ID", 0x9A: "MFR_MODEL",
    0x9B: "MFR_REVISION", 0x9C: "MFR_LOCATION", 0x9D: "MFR_DATE",
    0x9E: "MFR_SERIAL", 0xA0: "MFR_VIN_MIN", 0xA1: "MFR_VIN_MAX",
    0xA2: "MFR_IIN_MAX", 0xA3: "MFR_PIN_MAX", 0xA4: "MFR_VOUT_MIN",
    0xA5: "MFR_VOUT_MAX", 0xA6: "MFR_IOUT_MAX", 0xA7: "MFR_POUT_MAX",
    0xC0: "MFR_MAX_TEMP_1", 0xC1: "MFR_MAX_TEMP_2",
    0xC2: "MFR_MAX_TEMP_3",
}

def read_slot(blob: bytes, pc: int) -> int:
    if pc & 1:
        raise ValueError(f"PC must be even: 0x{pc:X}")
    index = pc // 2
    offset = HEADER_END + index * RECORD_SIZE
    raw = blob[offset:offset + RECORD_SIZE]
    if len(raw) != RECORD_SIZE:
        raise ValueError(f"PC 0x{pc:X} is outside the payload")
    return int.from_bytes(raw[:3], "little")

def read_psv_byte(blob: bytes, ea: int, psvpag: int = 0) -> int:
    if not 0x8000 <= ea <= 0xFFFF:
        raise ValueError(f"PSV data address out of window: 0x{ea:04X}")
    # Wn bit 0 selects the byte; remaining address bits map to program PC.
    pc = ((psvpag & 0xFF) << 15) | (ea & 0x7FFE)
    word = read_slot(blob, pc) & 0xFFFF
    return (word >> (8 * (ea & 1))) & 0xFF

def crc8_poly07(value: int) -> int:
    crc = value & 0xFF
    for _ in range(8):
        crc = (((crc << 1) ^ 0x07) if (crc & 0x80) else (crc << 1)) & 0xFF
    return crc

def rcall_target(pc: int, word: int) -> int:
    offset = word & 0xFFFF
    if offset & 0x8000:
        offset -= 0x10000
    return (pc + 2 + (offset << 1)) & 0x7FFFFF

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("payload", help="095HR5_190AD_00.3D.67 extracted payload")
    ap.add_argument("--csv", default="D1600E_00.3D.67_PMBus_commands.csv")
    args = ap.parse_args()
    blob = Path(args.payload).read_bytes()
    if len(blob) != 86340:
        raise SystemExit(f"Unexpected payload size: {len(blob)}")
    if blob[0x00:0x20].split(b"\n")[0] == b"":
        raise SystemExit("Invalid header")
    if b"00.3D.67" not in blob[:0x144] or b"095HR5A00" not in blob[:0x144]:
        raise SystemExit("Unexpected firmware identity; refusing analysis")

    pairs = []
    for pc in range(CMD_TABLE_START, CMD_TABLE_END + 1, 4):
        command = read_slot(blob, pc) & 0xFFFF
        handler = read_slot(blob, pc + 2) & 0xFFFF
        pairs.append((command, handler, pc))
    if len(pairs) != 85:
        raise SystemExit(f"Unexpected command table size: {len(pairs)}")

    low = [read_psv_byte(blob, CRC_LOW_PSV + i, 0) for i in range(16)]
    high = [read_psv_byte(blob, CRC_HIGH_PSV + i, 0) for i in range(16)]
    expected_low = [crc8_poly07(i) for i in range(16)]
    expected_high = [crc8_poly07(i << 4) for i in range(16)]

    call_word = read_slot(blob, 0x410C)
    call_target = rcall_target(0x410C, call_word)
    address_set = (read_slot(blob, 0x6F56), read_slot(blob, 0x6F58), read_slot(blob, 0x6F5A))

    with open(args.csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["command", "name", "handler_pc", "table_pc"])
        for command, handler, pc in pairs:
            writer.writerow([f"0x{command:02X}", NAMES.get(command, "vendor/unknown"),
                             f"0x{handler:04X}", f"0x{pc:04X}"])

    print(f"Command table entries: {len(pairs)}")
    print(f"CRC8 low table matches poly 0x07: {low == expected_low}")
    print(f"CRC8 high table matches poly 0x07: {high == expected_high}")
    print("CRC8 low :", " ".join(f"{x:02X}" for x in low))
    print("CRC8 high:", " ".join(f"{x:02X}" for x in high))
    print(f"RCALL at 0x410C: 0x{call_word:06X} -> 0x{call_target:06X}")
    print("Address setup words:", " ".join(f"0x{x:06X}" for x in address_set))
    print(f"CSV written: {args.csv}")
    for command, handler, pc in pairs:
        print(f"0x{command:02X} {NAMES.get(command, 'vendor/unknown'):24s} -> 0x{handler:04X} (table PC 0x{pc:04X})")

if __name__ == "__main__":
    main()
