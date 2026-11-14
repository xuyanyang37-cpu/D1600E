# D1600E / 95HR5 — dsPIC vector and PMBus dispatch investigation (evidence log)

Date: 2026-11-14

## Scope and input provenance

This pass used the previously generated `instruction_words.csv` (21,504 records) and the user's earlier PMBus test log. The original 86,340-byte payload was not mounted in the current analysis runtime, so no fresh byte-for-byte decode or instruction execution was performed in this pass.

Payload identity recorded by the earlier analysis:
- File: `095HR5_190AD_00.3D.67_extracted.bin`
- Size: 86,340 bytes
- SHA-256: `eedae0cd8d92e87ca12516c5cebfd80feb23462c424ec25eee10dc5ff40deed0`
- Package family: Delta 1600W / PN 95HR5 / firmware 00.3D.67
- Internal image label: `095HR5A00`
- Board reported by user: `95HR5A05PS` / D1600E-S0

The A00-vs-A05PS revision relationship remains unverified. Do not flash this payload to the A05PS board.

## 1. 24-bit record map — measured from the CSV

The CSV contains 21,504 records. Each record maps to four payload bytes beginning at file offset `0x144`; the first three bytes are represented as a 24-bit value and the fourth byte is recorded as padding. The CSV's candidate PC field increments by two per record. This is a useful candidate mapping, not yet a validated dsPIC program-memory address map.

Observed anchors:
- Record 0: candidate PC `0x000000`, file offset `0x000144`, word `0x040C00`.
- Records 0–127 cover candidate PC `0x000000–0x0000FE`.
- Within those first 128 records, `0x001018` appears 113 times. Several non-default entries are present, including `0x003E06`, `0x005F0A`, `0x007BB4`, `0x00778A`, `0x005EEC`, `0x006FA2`, `0x006F3C`, `0x007404`, `0x00740A`, and `0x0072C2`.
- Candidate PC `0x001018` maps to record 2060 and file offset `0x002174`; its first words are `DA4000 FE0000 B90A02 B91B00 B80002 420081 430081 060000 B82260 200206 D00000 D28081 D28204 D28285 A00000 ...`.
- A long erased-looking interval exists in the CSV (many `0xFFFFFF` records), followed by structured words around candidate PC `0x000C00` (record 1536; file offset `0x001944`).

Interpretation:
- The first 128 records have the shape expected of a vector/entry table, with many entries sharing the same candidate target `0x001018`. A common default ISR/trap target is a plausible hypothesis, not a proven function label.
- The block at candidate PC `0x001018` is a high-priority disassembly entry point because it is referenced repeatedly by the vector-like region.
- The 4-byte stride and zero padding byte are consistent with 24-bit program words stored in 32-bit records, but endian, word packing, PC scaling, and instruction boundaries must still be validated against dsPIC33FJ64GS606 documentation or an actual ICSP dump.

## 2. PMBus command-dispatch evidence from prior bench log

Working 7-bit address recorded for the user's board: `0x58`. This is a bench/project observation, not derived from the firmware image.

### Standard command IDs observed in the log

| Command | Code | Logged result | Evidence status |
|---|---:|---|---|
| VOUT_MODE | `0x20` | `0xFF` | Observed readback; may be unsupported, invalid, or a transaction/format issue |
| VOUT_COMMAND | `0x21` | `0xFFFF` | Observed readback; not evidence of a valid setpoint |
| VOUT_MAX | `0x24` | `0xFFFF` | Observed readback; not evidence of a valid limit |
| STATUS_WORD | `0x79` | `0x0002` | Observed |
| STATUS_CML | `0x7E` | `0xE0` | Observed; bit meaning not decoded here |
| READ_VOUT | `0x8B` | `0x18DF` | Observed raw word |
| READ_IOUT | `0x8C` | `0xC800` | Observed raw word; scaling/sign not established |
| READ_TEMPERATURE_1/2/3 | `0x8D/0x8E/0x8F` | `0x002E/0x0023/0x0028` | Observed; corresponds to 46/35/40 only under the user's existing interpretation |
| READ_FAN_SPEED_1 | `0x90` | `0x2117` in one capture | Observed raw word; RPM conversion depends on the PSU's encoding |

The log also reports CAPABILITY `0x90`, but this note does not decode its bit fields.

### Vendor-register experiments already present in the log

- Writes to register `0xE1` from `0x0000` to `0x0050` read back the written values. During one sweep, the fan raw reading drifted from `0x2334` to `0x2186`, while VOUT remained mostly `0x18DF` with occasional `0x18E7` samples. Another sweep showed little or no fan change.
- Writes to register `0xE3` from `0xF000` through `0xF0F0` read back the written values. VOUT remained mostly `0x18DF`, with occasional `0x18E7`; fan values changed gradually in one run and were stable in another.
- The log shows an application-side mapping such as 10,000 mV -> E3 value 0x0067 and 11,000 mV -> E3 value 0x0045. This is an application experiment, not proof that E3 is a voltage setpoint. No measured output-voltage step response establishes causality.

Safety conclusion: do not repeat vendor-register writes on the live PSU to probe semantics. Readback only proves a value was stored/read back; it does not prove the register controls voltage, fan, or current.

## 3. Current command-dispatch hypothesis

A candidate receive/dispatch path to test in disassembly is:

1. I2C/SMBus peripheral initialization and slave address setup.
2. Address match for the reported 7-bit address (check whether firmware stores 7-bit or shifted address).
3. Receive ISR or peripheral event handler captures command byte and optional data bytes.
4. Transaction state machine distinguishes command-only read, byte read, word read, and block transfers.
5. Command lookup / switch dispatch selects telemetry handler or vendor-register handler.
6. Handler obtains a measurement/configuration variable, applies scaling/formatting, and prepares response bytes.
7. Transmit ISR shifts response and possibly PEC.

This is a search plan, not a recovered implementation. In particular, PEC use, repeated-start handling, page selection, command whitelist, and vendor write authorization remain unknown.

## 4. Highest-priority reverse-engineering tasks

1. Validate the image packing: compare the 4-byte records with a read-only ICSP dump from the actual board, or use a known-good dsPIC33FJ64GS606 programming image as a reference.
2. Confirm the program counter mapping and dsPIC33F instruction endian/word order. Do not assume a generic PIC16 decoder is suitable.
3. Seed disassembly at the vector-like table and candidate PC `0x001018`; decode any two-word GOTO/CALL forms before creating cross-references.
4. Identify the structured code block around candidate PC `0x000C00` and follow its calls into the main loop/initialization.
5. Search peripheral setup for I2C module registers, interrupt enables, slave address registers, and ISR entry points.
6. Trace command-byte comparisons and response-buffer writes; then map command IDs to handlers.
7. Correlate handler variables with existing telemetry captures. Keep all unknown register semantics labelled as hypotheses.

## 5. What is still required for a genuine instruction-level result

The original file `095HR5_190AD_00.3D.67_extracted.bin` (86,340 bytes) or an unmodified read-only ICSP dump must be available to the analysis runtime. The CSV is a derived word listing and does not preserve all original container/header context. The actual MCU count/image-to-chip mapping must also be established; the board has been reported to contain two dsPIC33FJ64GS606 devices, but this payload has not yet been proven to contain both MCU images.

No assembly listing, CFG, command handler address, or C pseudocode is claimed by this report.
