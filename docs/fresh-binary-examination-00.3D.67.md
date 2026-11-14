# D1600E firmware 00.3D.67 — fresh binary examination

Date: 2026-11-14
Input: `/mnt/data/095HR5_190AD_00.3D.67_extracted(1).bin`

## 1. Exact file verification

The uploaded file was read directly in this session.

- Size: 86,340 bytes (`0x15144`)
- SHA-256: `eedae0cd8d92e87ca12516c5cebfd80feb23462c424ec25eee10dc5ff40deed0`
- MD5 of the entire uploaded file: `e90a05c2ec6268a72ccaba65a3d88291`
- First 7 newline-terminated header fields:
  1. `e2b8c1d013a387ced736076bf453154c`
  2. `2`
  3. `00.3D.67`
  4. `1`
  5. `095HR5A00`
  6. `1`
  7. `000190AD`

The text header ends at file offset `0x42`; opaque/binary data begins at `0x43`. The file contains a 4-byte-aligned record area beginning at `0x144`, with 21,504 records through offset `0x15140`. Every record has three little-endian data bytes followed by a zero fourth byte. The last eight bytes include erased-looking fill followed by `CD AB 00 00 C0 62 F1 00`.

Important: the record area is a structured image representation, not proof that every 24-bit record is executable code. Header, vector entries, jump stubs, code, erased gaps, and possible configuration/footer data must be distinguished.

## 2. Strong dsPIC program-memory layout correlation

The dsPIC33FJ64GS606 family data sheet states:
- Program space is 24 bits wide.
- Program Counter addresses instructions on even program addresses.
- Reset/GOTO/vector regions occupy the low program addresses.
- For the dsPIC33FJ64GS606, the interrupt vector table is in the low region and the alternate vector table begins at `0x000104`; user program memory begins at `0x000200`.

Microchip sources:
- Device data sheet PDF: https://ww1.microchip.com/downloads/en/DeviceDoc/70000591f.pdf
- Microchip device page: https://www.microchip.com/en-us/product/dspic33fj64gs606
- Microchip 16-bit MCU architecture overview: https://developerhelp.microchip.com/xwiki/bin/view/products/mcu-mpu/16bit-mcu/architecture/

The record values around the start of the image strongly resemble a reset/vector area:
- Record 0 at file offset `0x144`: `0x040C00`
- Record 1 at `0x148`: `0x000000`
- Record 2 at `0x14C`: `0x0190AD`
- Record 3 at `0x150`: `0x000200`
- Following entries repeatedly contain `0x001018`, with non-default targets such as `0x003E06`, `0x005F0A`, `0x007BB4`, `0x00778A`, `0x005EEC`, `0x006FA2`, `0x006F3C`, `0x007404`, `0x00740A`, and `0x0072C2`.

The second table-like region starts at file offset `0x34C` (record 130), which corresponds to candidate program address `0x000104` if each 24-bit record advances the dsPIC PC by two. This exact match with the documented alternate vector table boundary is strong evidence that the record-to-PC mapping is plausible.

Caveat: the first records appear to include reset/vector long-branch pairs. The record index-to-PC mapping is therefore useful as a candidate map, but each vector slot's instruction width and target encoding must be validated before labeling every record as a standalone instruction.

## 3. Candidate branch/stub table at PC 0x000C00

At record 1536 / file offset `0x1944`, candidate PC is `0x000C00`. This region contains repeated pairs where a first 24-bit value begins with `0x04` and the following 24-bit value is zero:

| Candidate PC | First word | Following word | Candidate target encoded in first word |
|---:|---:|---:|---:|
| `0x0C00` | `040C40` | `000000` | `0x0C40` |
| `0x0C04` | `0472C2` | `000000` | `0x72C2` |
| `0x0C08` | `047404` | `000000` | `0x7404` |
| `0x0C0C` | `046F3C` | `000000` | `0x6F3C` |
| `0x0C10` | `045EEC` | `000000` | `0x5EEC` |
| `0x0C14` | `045F0A` | `000000` | `0x5F0A` |
| `0x0C18` | `04778A` | `000000` | `0x778A` |
| `0x0C1C` | `046FA2` | `000000` | `0x6FA2` |
| `0x0C20` | `047BB4` | `000000` | `0x7BB4` |
| `0x0C24` | `043E06` | `000000` | `0x3E06` |
| `0x0C28` | `0190AD` | `000000` | not decoded |
| `0x0C2C` | `045594` | `000000` | `0x5594` |
| `0x0C30` | `04740A` | `000000` | `0x740A` |

This resembles a table of two-word GOTO/branch stubs or a function-entry dispatch table. Several targets overlap values observed in the vector-like region. The target interpretation is a strong hypothesis based on opcode shape and repeated layout; it has not yet been confirmed by a dsPIC instruction decoder.

The region from candidate PC `0x0C40` begins with less repetitive values:
`22874F 22BF0E 88010E 000000 07000C 279300 200001 07001F 200000 E00000 320002 020000 ...`
This is a higher-priority candidate for executable code than the preceding stub table.

## 4. Erased and populated regions

Using 4-byte records from file offset `0x144`:
- Records 0–127: populated vector/header-like area.
- Records 128–129: `0xFFFFFF` gap.
- Records 130–255: populated second table-like area.
- Records 256–1535: `0xFFFFFF` erased-looking area.
- Records 1536–1561: populated branch/stub-like table.
- Records 1562–1567: `0xFFFFFF` gap.
- Records 1568–16159: large populated region, likely main code/data region.
- Records 16160–21501: `0xFFFFFF` erased-looking fill.
- Records 21502–21503: non-FF footer words.

This suggests the payload is a sparse flash image or an encoded programming image with explicit erased regions, rather than a dense 86 KB stream of instructions.

## 5. PMBus protocol — what is and is not established

The uploaded firmware bytes have not yet yielded a decoded PMBus command table or handler addresses. The following values come from the user's prior live-bus logs, not from static firmware decoding:

- Reported 7-bit bus address: `0x58`
- `READ_VOUT (0x8B)` -> raw `0x18DF`
- `READ_IOUT (0x8C)` -> raw `0xC800`
- `STATUS_WORD (0x79)` -> `0x0002`
- `READ_TEMPERATURE_1/2/3 (0x8D/0x8E/0x8F)` -> `0x002E / 0x0023 / 0x0028`
- `READ_FAN_SPEED_1 (0x90)` -> observed raw values around `0x2117` in one capture
- `VOUT_MODE (0x20)` -> `0xFF` and `VOUT_COMMAND (0x21)` -> `0xFFFF` in the earlier test application

Vendor commands `0xE1` and `0xE3` were written/read back in previous experiments. Readback does not prove they are voltage/fan controls. Do not perform further blind writes.

## 6. Next reverse-engineering pass

1. Implement/obtain a dsPIC33F/PIC24H instruction decoder that supports the 24-bit word format and two-word instructions (especially GOTO/CALL).
2. Decode the reset instruction at PC 0 and vector pairs; validate branch targets against the table at PC `0x0C00`.
3. Disassemble from candidate PC `0x0C40`, then follow calls and cross-references to targets `0x3E06`, `0x5594`, `0x5EEC`, `0x5F0A`, `0x6F3C`, `0x6FA2`, `0x72C2`, `0x7404`, `0x740A`, `0x778A`, `0x7BB4`, and `0x90AD`.
4. Search disassembly for I2C peripheral setup, slave-address initialization, I2C interrupt vectors, receive/transmit state machines, and command-byte comparisons.
5. Map the command handlers only after control-flow references and data-flow are established.

## 7. Safety / confidence labels

- Confirmed: exact uploaded-file size and SHA-256; text header fields; 4-byte record structure; zero padding bytes; sparse erased regions; correspondence of the second table boundary with documented alternate-vector address under the candidate PC map.
- Strong hypothesis: 24-bit little-endian words; record-to-PC mapping; vector/branch-stub interpretation; code begins near candidate PC `0x0C40`.
- Not established: that this payload is the exact executable image for the user's `95HR5A05PS` board revision; whether it contains one or two MCU images; actual PMBus command handler addresses; E1/E3 semantics; PEC behavior; writable VOUT support.

No firmware was modified, no PSU register writes were performed in this analysis pass, and no programming operation was attempted.
