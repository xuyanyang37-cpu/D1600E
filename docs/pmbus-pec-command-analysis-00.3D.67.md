# Dell Delta D1600E 00.3D.67 – PMBus command table and PEC analysis

## 1. Image identity and safety boundary

Payload: `095HR5_190AD_00.3D.67_extracted(1).bin`

- Size: 86,340 bytes (`0x15144`)
- SHA-256: `eedae0cd8d92e87ca12516c5cebfd80feb23462c424ec25eee10dc5ff40deed0`
- Header model: `095HR5A00`
- Firmware version: `00.3D.67`
- Program record area begins at file offset `0x144`; each record is 4 bytes: 24-bit little-endian program word plus padding byte.

The user's PCB marking is `95HR5A05PS`; this payload header says `095HR5A00`. Compatibility is not proven. Do not flash this image to the PSU.

## 2. I2C1 slave address is set to 0x58

The device data sheet maps I2C1 registers as follows: I2C1RCV `0x0200`, I2C1TRN `0x0202`, I2C1BRG `0x0204`, I2C1CON `0x0206`, I2C1STAT `0x0208`, I2C1ADD `0x020A`, I2C1MSK `0x020C`. See Microchip DS70591, Table 4-26: https://ww1.microchip.com/downloads/en/DeviceDoc/70591D.pdf

Verified instruction path:

| PC | Word | Decode |
|---|---:|---|
| `0x00410C` | `0x071724` | RCALL target `0x006F56` |
| `0x006F56` | `0x200580` | MOV #`0x0058`, W0 |
| `0x006F58` | `0x881050` | MOV W0, I2C1ADD (`0x020A`) |
| `0x006F5A` | `0x060000` | RETURN |

A second code path at `0x007152–0x007154` also loads `0x0058` and writes it to I2C1ADD.

**Conclusion:** the firmware configures the I2C1 own-address register with `0x58`. This directly corroborates the user's observed PMBus address. The I2C1CON A10M bit (bit 10) still needs a definitive value trace; therefore do not overstate 7-bit versus 10-bit mode from this instruction alone. If A10M=0, `0x58` is the 7-bit address.

## 3. I2C1 slave ISR and register evidence

The dsPIC33FJ64GS606 SI2C1 vector at PC `0x0034` contains `0x006FA2`; the alternate SI2C1 vector at `0x0134` also points to `0x006FA2`.

Selected code evidence:

| PC | Word | Interpretation |
|---|---:|---|
| `0x006FAE` | `0x801000` | Read I2C1RCV (`0x0200`) into W0 |
| `0x006FB4` | `0xA9C208` | Clear I2C1STAT bit 6, I2COV |
| `0x006FB8` | `0xBFC208` | Read I2C1STAT (`0x0208`) |
| `0x006F7C` | `0x881011` | Write W1 to I2C1TRN (`0x0202`) |
| `0x006F94` | `0x881010` | Write W0 to I2C1TRN |
| `0x006F9E` | `0x881010` | Write W0 to I2C1TRN |
| `0x007036` | `0xA88207` | Set I2C1CON bit 12, SCLREL |

The ISR also tests I2C1STAT bit 2 (R/W) and bit 5 (D/A), matching the device data-sheet definitions. This is strong evidence of a real I2C1 slave state machine, including receive, transmit, overflow handling and clock release.

## 4. Confirmed PMBus command-to-handler table

### Table location and access

There are 85 pairs from program PC `0x14D8` through `0x162A`. Each pair is:

1. 16-bit command code
2. 16-bit handler PC address

Startup code:
- PC `0x000C62`: clear CORCON.PSV bit 2
- PC `0x000C6A`: load W0 = 0
- PC `0x000C6C`: write W0 to PSVPAG
- PC `0x000C6E`: set CORCON.PSV bit 2

The table is accessed through PSV data address `0x94D8`, which maps to program PC `0x14D8` when PSVPAG=0. Microchip's PSV documentation states that the upper data-space window `0x8000–0xFFFF` maps a selected program-memory page, and the lower 15 address bits map to the corresponding program-memory address: https://ww1.microchip.com/downloads/en/DeviceDoc/70203c.pdf

The I2C processing helper at `0x00280A` loads table base `0x94D8`, loads a handler pointer from the table, then executes an indirect `CALL W0` at PC `0x00283A`. The I2C1 ISR calls this helper at PC `0x007022`.

### Full extracted table

| Command | Name / classification | Handler PC |
|---:|---|---:|
| 0x1A | QUERY | 0x1DA8 |
| 0x30 | COEFFICIENTS | 0x2342 |
| 0x3A | FAN_CONFIG_12 | 0x1E62 |
| 0x3B | FAN_COMMAND_1 | 0x1E4E |
| 0x78 | STATUS_BYTE | 0x1BC8 |
| 0x79 | STATUS_WORD | 0x1B90 |
| 0x7A | STATUS_VOUT | 0x1BFA |
| 0x7B | STATUS_IOUT | 0x1C2C |
| 0x7C | STATUS_INPUT | 0x1C5E |
| 0x7D | STATUS_TEMPERATURE | 0x1C90 |
| 0x7E | STATUS_CML | 0x1CC2 |
| 0x7F | STATUS_OTHER | 0x1D1A |
| 0x81 | STATUS_FAN_12 | 0x1D30 |
| 0x86 | unclassified | 0x1D46 |
| 0x87 | unclassified | 0x1D68 |
| 0x88 | READ_VIN | 0x1AC8 |
| 0x89 | READ_IIN | 0x1AE2 |
| 0x8B | READ_VOUT | 0x1AFC |
| 0x8C | READ_IOUT | 0x1B16 |
| 0x8D | READ_TEMPERATURE_1 | 0x1E00 |
| 0x8E | READ_TEMPERATURE_2 | 0x1E1A |
| 0x8F | READ_TEMPERATURE_3 | 0x1E34 |
| 0x90 | READ_FAN_SPEED_1 | 0x1DE0 |
| 0x96 | READ_POUT | 0x1B5C |
| 0x97 | READ_PIN | 0x1B76 |
| 0x98 | PMBUS_REVISION | 0x1D94 |
| 0x9F | unclassified | 0x1D9E |
| 0xA7 | MFR_POUT_MAX | 0x21F6 |
| 0xB0 | vendor/unknown | 0x1EBA |
| 0xB1 | vendor/unknown | 0x1ECA |
| 0xB2 | vendor/unknown | 0x1EDE |
| 0xB3 | vendor/unknown | 0x1EFE |
| 0xD0 | vendor/unknown | 0x1F26 |
| 0xD2 | vendor/unknown | 0x1F3E |
| 0xD5 | vendor/unknown | 0x20D2 |
| 0xE8 | vendor/unknown | 0x22E8 |
| 0xE0 | vendor/unknown | 0x22F2 |
| 0xE1 | vendor/unknown | 0x2308 |
| 0xE2 | vendor/unknown | 0x2316 |
| 0xE3 | vendor/unknown | 0x2324 |
| 0x19 | CAPABILITY | 0x1D8A |
| 0x99 | MFR_ID | 0x1F5C |
| 0x9A | MFR_MODEL | 0x1F7A |
| 0x9B | MFR_REVISION | 0x1F94 |
| 0xD7 | vendor/unknown | 0x1F48 |
| 0xE4 | vendor/unknown | 0x2140 |
| 0xE5 | vendor/unknown | 0x214A |
| 0xE6 | vendor/unknown | 0x216A |
| 0x06 | PAGE_PLUS_READ | 0x247C |
| 0x1B | SMBALERT_MASK | 0x25D4 |
| 0x00 | PAGE | 0x1ABE |
| 0xA0 | MFR_VIN_MIN | 0x218A |
| 0xA1 | MFR_VIN_MAX | 0x2196 |
| 0xA2 | MFR_IIN_MAX | 0x21A4 |
| 0xA3 | MFR_PIN_MAX | 0x21B2 |
| 0xA4 | MFR_VOUT_MIN | 0x21DA |
| 0xA5 | MFR_VOUT_MAX | 0x21CC |
| 0xA6 | MFR_IOUT_MAX | 0x21E8 |
| 0xA8 | vendor/unknown | 0x2204 |
| 0xA9 | vendor/unknown | 0x2210 |
| 0xAA | vendor/unknown | 0x221C |
| 0xAB | vendor/unknown | 0x2260 |
| 0xD8 | vendor/unknown | 0x1F52 |
| 0xDA | vendor/unknown | 0x22A6 |
| 0xEB | vendor/unknown | 0x23AA |
| 0xF0 | vendor/unknown | 0x246C |
| 0x9C | MFR_LOCATION | 0x1FAE |
| 0x9D | MFR_DATE | 0x1FFC |
| 0x9E | MFR_SERIAL | 0x20C0 |
| 0x40 | VOUT_OV_FAULT_LIMIT | 0x1E6C |
| 0x44 | VOUT_UV_FAULT_LIMIT | 0x1E7A |
| 0x46 | IOUT_OC_FAULT_LIMIT | 0x1E88 |
| 0x4A | IOUT_OC_WARN_LIMIT | 0x1E9C |
| 0x5D | IIN_OC_WARN_LIMIT | 0x1DB8 |
| 0x6B | PIN_OP_WARN_LIMIT | 0x1DCC |
| 0xC0 | MFR_MAX_TEMP_1 | 0x22C0 |
| 0xC1 | MFR_MAX_TEMP_2 | 0x22D4 |
| 0xC2 | MFR_MAX_TEMP_3 | 0x22DE |
| 0xDC | vendor/unknown | 0x261A |
| 0xDD | vendor/unknown | 0x1CF4 |
| 0xDE | vendor/unknown | 0x26BA |
| 0xED | vendor/unknown | 0x26EC |
| 0xDF | vendor/unknown | 0x26F6 |
| 0xF2 | vendor/unknown | 0x27DA |
| 0xF1 | vendor/unknown | 0x27F2 |

Names for standard commands were cross-checked against the Linux PMBus command definitions: https://github.com/torvalds/linux/blob/master/drivers/hwmon/pmbus/pmbus.h. Entries labelled `vendor/unknown` or `unclassified` are intentionally not guessed.

### Important supported commands

The firmware table explicitly contains:
- `0x8B READ_VOUT → 0x1AFC`
- `0x8C READ_IOUT → 0x1B16`
- `0x8D/0x8E/0x8F READ_TEMPERATURE_1/2/3 → 0x1E00/0x1E1A/0x1E34`
- `0x90 READ_FAN_SPEED_1 → 0x1DE0`
- `0x96 READ_POUT → 0x1B5C`
- `0x97 READ_PIN → 0x1B76`
- `0x78–0x7F STATUS_* commands`

This is direct firmware evidence, not an inference from standard command numbers.

### READ response buffer

The READ_VOUT handler at `0x1AFC`:
- reads selector/state RAM `0x0E5C`;
- selects one of two 16-bit source words: `0x0EAA` or `0x0F06`;
- writes the low/high response bytes to `0x0E0F` and `0x0E10`;
- sets response length `0x0E57 = 2`;
- returns.

The corresponding handlers use these source candidates:

| Command | Handler | Source A | Source B |
|---|---:|---:|---:|
| READ_VOUT | `0x1AFC` | `0x0EAA` | `0x0F06` |
| READ_IOUT | `0x1B16` | `0x0EAC` | `0x0F08` |
| READ_TEMPERATURE_1 | `0x1E00` | `0x0EB2` | `0x0F0E` |
| READ_TEMPERATURE_2 | `0x1E1A` | `0x0EB0` | `0x0F0C` |
| READ_TEMPERATURE_3 | `0x1E34` | `0x0EB4` | `0x0F10` |
| READ_FAN_SPEED_1 | `0x1DE0` | — | `0x0F12` |
| READ_POUT | `0x1B5C` | `0x0EAE` | `0x0F0A` |
| READ_PIN | `0x1B76` | `0x0EA8` | `0x0F04` |

The meaning of selector `0x0E5C` and the units/scaling of the source words are not yet resolved. The user's raw `READ_VOUT=0x18DF` is consistent with a two-byte response but does not by itself identify which source path was selected.

The command table does not contain `0x20 VOUT_MODE`, `0x21 VOUT_COMMAND`, or `0x24 VOUT_MAX`. This is consistent with the user's earlier all-ones reads, but alternate handling outside this table has not been ruled out.

## 5. PEC / CRC-8 discovery

### Table data

Program PC `0x1882` contains the 16-byte low-nibble table:

`00 07 0E 09 1C 1B 12 15 38 3F 36 31 24 23 2A 2D`

Program PC `0x1892` contains the 16-byte high-nibble table:

`00 70 E0 90 C7 B7 27 57 89 F9 69 19 4E 3E AE DE`

These are the two 16-entry nibble lookup tables for CRC-8 polynomial `0x07` (SMBus PEC). The SMBus 3.2 specification defines PEC as CRC-8 using polynomial `x^8 + x^2 + x + 1`, calculated over the transaction bytes in receive order, including address, command and data: https://www.smbus.org/specs/SMBus_3_2_20220112.pdf

### Helper function

The helper at PC `0x00332A`:
- accesses working state at RAM `0x13F0`;
- XORs a working byte with the state;
- extracts a nibble;
- loads lookup bases `0x9892` and `0x9882`;
- performs two PSV table lookups and XORs their results;
- returns the updated CRC-like byte.

The I2C1 path calls this helper at multiple points, including PCs `0x006FDA`, `0x006FF6`, and via the transmit/dispatch helpers.

**Conclusion:** the firmware contains a table-driven CRC-8 engine using the exact SMBus PEC polynomial. Given its call sites in the I2C1 handler, this is high-confidence evidence of PMBus/SMBus PEC support. The exact initial value, byte sequence, read/write coverage and PEC transmit/compare branch still need to be reconstructed before writing a byte-for-byte compatible ESP32 implementation.

## 6. Manufacturer-specific commands E1 and E3

The command table maps:
- `0xE1 → 0x2308`
- `0xE3 → 0x2324`

The read-response handler at `0x2308` calls helper `0x3B94`, which reads internal RAM `0x13AA`; the handler returns two bytes through `0x0E0F/0x0E10`.

The handler at `0x2324` calls `0x3B4E` (which reads RAM `0x1398`) and `0x33D6`, then returns two bytes.

This establishes that E1/E3 are real implemented command entries and identifies their read-side data paths. It does **not** yet establish what a write transaction to E1 or E3 changes. Do not use the previous E1/E3 bench correlation as proof of fan or voltage control.

## 7. What remains to be decoded

1. Reconstruct the exact CRC8 update byte order and PEC inclusion points (address, command, data, repeated-start, read direction).
2. Trace the write-side command parser to determine what writes to E1/E3 actually modify.
3. Identify the source/scaling of `0x0EAA`, `0x0EAC`, temperature and fan variables.
4. Resolve I2C1CON.A10M (bit 10) to prove 7-bit versus 10-bit address mode.
5. Identify why `VOUT_MODE 0x20` and `VOUT_COMMAND 0x21` are absent from the 85-entry table.
6. Verify whether this one payload corresponds to one MCU image or whether a second MCU has a separate image.

No PMBus writes, flash writes or firmware flashing were performed.
