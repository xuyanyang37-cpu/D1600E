# D1600E / 95HR5 PMBus protocol notes

## Evidence labels
- **Standard PMBus definition:** command code/name from PMBus convention; does not prove this PSU implements it.
- **Prior bench observation:** values previously reported by the user; not extracted from firmware 00.3D.67.
- **Unknown for this firmware:** requires read-only capture or validated disassembly.

## Addressing
The current working 7-bit PMBus address reported for the user's D1600E-S0 is **`0x58`** (project context; user-corrected). In Arduino `Wire` APIs, use 7-bit `0x58`; do not pass shifted wire address `0xB0` as the device address.

For 7-bit address 0x58:
- write address byte on the wire: `0xB0`
- read address byte on the wire: `0xB1`

This is a project/bench observation, not confirmed from the Dell 00.3D.67 payload.

## Standard PMBus command reference

Presence here is **not** proof that the 95HR5 firmware supports the command.

| Command | Code | Standard meaning |
|---|---:|---|
| PAGE | `0x00` | Select page |
| OPERATION | `0x01` | Output on/off/margin operation |
| CLEAR_FAULTS | `0x03` | Clear latched fault status |
| WRITE_PROTECT | `0x10` | Write protection control |
| CAPABILITY | `0x19` | Capability information |
| VOUT_MODE | `0x20` | Output voltage data format |
| VOUT_COMMAND | `0x21` | Output voltage setpoint |
| VOUT_MAX | `0x24` | Maximum output voltage |
| VOUT_MARGIN_HIGH | `0x25` | High margin target |
| VOUT_MARGIN_LOW | `0x26` | Low margin target |
| VOUT_TRANSITION_RATE | `0x27` | Output transition rate |
| COEFFICIENTS | `0x30` | Direct-format coefficients |
| STATUS_WORD | `0x79` | Combined status word |
| STATUS_VOUT | `0x7A` | Output voltage status |
| STATUS_IOUT | `0x7B` | Output current status |
| STATUS_INPUT | `0x7C` | Input status |
| STATUS_TEMPERATURE | `0x7D` | Temperature status |
| STATUS_CML | `0x7E` | Communication/memory/logic status |
| STATUS_OTHER | `0x7F` | Other status |
| READ_VIN | `0x88` | Input voltage measurement |
| READ_IIN | `0x89` | Input current measurement |
| READ_VOUT | `0x8B` | Output voltage measurement |
| READ_IOUT | `0x8C` | Output current measurement |
| READ_TEMPERATURE_1 | `0x8D` | Temperature measurement |
| READ_FAN_SPEED_1 | `0x90` | Fan speed measurement |

## Prior user-reported read-only observations

These are from earlier project measurements, not extracted from this firmware file.

| Item | Previously reported |
|---|---:|
| READ_VOUT raw | `0x18DF` |
| Approximate output | about 12.06 V (prior interpretation; re-check with live VOUT_MODE/scaling) |
| STATUS_WORD | `0x0002` |
| Fan speed | 4,256 RPM |
| Temperatures | 46 / 35 / 40 °C |
| Current working 7-bit address | `0x58` |

Do not assume the earlier voltage conversion is correct until the actual VOUT_MODE and device encoding are captured. `VOUT_MODE (0x20)` and `READ_VOUT (0x8B)` are different commands.

## Read-only capture plan
1. Capture bus idle level, SCL frequency, and clock stretching.
2. Confirm 7-bit address 0x58 by passive capture or non-invasive read-only identification.
3. Read one command at a time using the controller's documented PMBus/I²C read sequence.
4. Record address/RW, command byte, repeated START/STOP, returned byte count, byte order, ACK/NACK, and any PEC byte.
5. Read VOUT_MODE (0x20) before interpreting READ_VOUT (0x8B).
6. Repeat stable telemetry reads and compare with calibrated instruments where safe.
7. Do not test VOUT_COMMAND, OPERATION, CLEAR_FAULTS, WRITE_PROTECT, or vendor-specific writes until semantics and protection behavior are understood.

## PEC note
SMBus/PMBus PEC commonly uses CRC-8 polynomial `0x07`, initial value `0x00`, with address/RW and transaction bytes included in the CRC stream. Whether this PSU requires or returns PEC for a given transaction is **not established** by the current payload analysis. Verify through passive capture or controlled read-only transactions.

## Unknowns
- Whether 0x58 is used on every hardware revision.
- Supported command list and vendor-specific commands.
- Whether PEC is enabled, optional, or command-dependent.
- VOUT_MODE exponent and vendor scaling.
- READ_IOUT format/calibration.
- Fan command/control semantics and RPM conversion.
- Write protection/unlock behavior.
- Relationship between PMBus setpoint and UCC28950 analog feedback/COMP circuitry.

Repository rule: label each item as `measured`, `standard`, `derived`, or `hypothesis`. Do not promote a hypothesis to a confirmed register map without reproducible capture or code evidence.
