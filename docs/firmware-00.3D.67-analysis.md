# Dell Delta 1600W PSU 95HR5 — firmware 00.3D.67 analysis

## Scope and confidence

Analyzed payload: `095HR5_190AD_00.3D.67_extracted.bin`.

Package metadata identifies a Delta 1600W PSU, PN `95HR5`, firmware `00.3D.67`, internal image name `095HR5A00`, and token `000190AD`.

**Compatibility limit:** the user's physical PCB marking is `95HR5A05PS`, while this payload says `095HR5A00`. The shared 95HR5 family is evidence of a family relationship, not proof of safe cross-revision flashing. Do not flash without confirming exact hardware ID/revision and Dell applicability.

## Measured file facts

| Field | Result |
|---|---|
| Size | 86,340 bytes (`0x15144`) |
| SHA-256 | `eedae0cd8d92e87ca12516c5cebfd80feb23462c424ec25eee10dc5ff40deed0` |
| MD5 of complete file | `e90a05c2ec6268a72ccaba65a3d88291` |
| Header checksum text | `e2b8c1d013a387ced736076bf453154c` |
| Header checksum verification | Matches MD5 of bytes from offset `0x21` through EOF |
| Version | `00.3D.67` |
| Internal image label | `095HR5A00` |
| Internal token | `000190AD` |

The first 32 ASCII characters are checksum text; byte `0x20` is LF. Recalculation of MD5 over bytes beginning at `0x21` matched exactly.

## Observed layout

| File offset | Length | Observation | Interpretation |
|---|---:|---|---|
| `0x0000–0x003F` | 64 B | ASCII metadata lines | Header/checksum/version/product identifiers |
| `0x0040–0x01FF` | 448 B | Mixed high-entropy bytes followed by structured-looking values | Unclassified; do not label as encrypted or key material without evidence |
| `0x0200–0xFFFF` | 65,024 B | 16,256 records of 4 bytes; every fourth byte is `00` | Consistent with 24-bit words stored in 4-byte slots; dsPIC is a candidate from board context, not yet proven |
| `0x10000–0x1513B` | 20,796 B | Repeated `FF FF FF 00` | Erased/unused-looking fill in this representation |
| `0x1513C–0x15143` | 8 B | `CD AB 00 00 C0 62 F1 00` | Trailer candidate; meaning unknown |

Within the 4-byte word region there are 16,256 slots: 14,280 are neither all-zero nor erased-fill, 1,431 are `FF FF FF 00`, and 545 are `00 00 00 00`. This is structural analysis, **not a validated instruction disassembly**.

## Established vs unknown

### Established from this file
- It identifies itself as Delta 1600W / PN 95HR5 / firmware 00.3D.67.
- Internal image label is 095HR5A00; token is 000190AD.
- Header MD5 covers bytes from offset 0x21 to EOF and verifies.
- Main region has a regular 4-byte stride with high byte zero, compatible with a 24-bit word storage representation.

### Not established
- That this payload is specifically for PCB revision 95HR5A05PS.
- That the 4-byte words are definitely dsPIC33FJ64GS606 program memory.
- Reset/vector addresses, configuration words, device ID, calibration area.
- Device-specific PMBus address, command whitelist, scaling, write-unlock sequence, PEC policy, or voltage/current control algorithm.
- Source code, symbols, or human-readable protocol strings.

No PMBus implementation has been attributed to this binary yet. See the separate protocol note for standard command definitions and prior bench observations.

## Recommended next steps
1. Obtain a read-only ICSP dump from the actual 95HR5A05PS board and preserve it unchanged.
2. Identify the image encoding/address mapping by comparing the board dump with this update payload.
3. Confirm dsPIC33FJ64GS606 word packing and map reset/vector locations before disassembly.
4. Inspect configuration words and code-protection state without erasing or writing.
5. Capture PMBus traffic read-only: address, command, repeated-start/stop, byte order, PEC, response length.
6. Correlate observed PMBus commands with firmware call sites only after a trustworthy disassembly exists.
7. Assess any voltage command only after hardware feedback and protection limits are understood.

## Safety
This is an analysis artifact, not a validated programming image for the exact board. Do not flash, patch, or write PMBus control registers based on this report. A 1600 W server PSU contains hazardous mains and high-energy circuitry.
