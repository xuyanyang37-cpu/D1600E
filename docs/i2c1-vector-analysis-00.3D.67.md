# Dell D1600E 00.3D.67 – dsPIC33F vector and I2C1 entry analysis

## Scope and identity

Analyzed payload: `095HR5_190AD_00.3D.67_extracted(1).bin`

- Payload size: 86,340 bytes (`0x15144`)
- SHA-256: `eedae0cd8d92e87ca12516c5cebfd80feb23462c424ec25eee10dc5ff40deed0`
- Header model: `095HR5A00`
- Header build/internal ID: `000190AD`
- Firmware version: `00.3D.67`
- Binary program-record area starts at file offset `0x144`
- Program records: 21,504 × 4 bytes; each record is three little-endian instruction/address bytes followed by a zero pad byte.

**Hardware compatibility warning:** the target PCB has been identified by the user as `95HR5A05PS`, while this firmware header says `095HR5A00`. This analysis does not establish that these revisions are interchangeable. Do not flash this image based on this analysis.

## Confirmed reset path

The device data sheet says reset forces PC to zero and execution starts at address `0x000000`; a GOTO at that location redirects execution to startup code. Program addresses are word-addressed and advance by two.

The extracted records match the dsPIC33F GOTO encoding:

| PC | 24-bit slot | Meaning |
|---|---:|---|
| `0x000000` | `0x040C00` | GOTO first-stage address |
| `0x000002` | `0x000000` | second word of two-word GOTO |
| `0x000C00` | `0x040C40` | GOTO startup entry |
| `0x000C02` | `0x000000` | second word of GOTO |
| `0x000C40` | `0x22874F` | first instruction at candidate startup entry |

Thus the observed reset chain is **PC 0x000000 → 0x000C00 → 0x000C40**. The instructions at `0x000C04–0x000C32` form a contiguous sequence of GOTO-like entries, but their role has not yet been established; do not label them as a confirmed dispatch table.

## I2C interrupt vector finding

The dsPIC33FJ64GS606 data sheet identifies:
- SI2C1 (I2C1 Slave Event) vector at PC `0x000034`
- MI2C1 (I2C1 Master Event) vector at PC `0x000036`
- SI2C2 at PC `0x000076`
- MI2C2 at PC `0x000078`
- AIVT is organized in the same manner as the standard IVT, with the SI2C1 alternate vector at PC `0x000134`.

Values extracted from this firmware:

| Vector | PC | Firmware vector value |
|---|---:|---:|
| SI2C1 | `0x000034` | `0x006FA2` |
| MI2C1 | `0x000036` | `0x001018` |
| SI2C2 | `0x000076` | `0x001018` |
| MI2C2 | `0x000078` | `0x001018` |
| AIVT SI2C1 | `0x000134` | `0x006FA2` |

At `0x001018`, the first two instruction slots are `0xDA4000` and `0xFE0000` (BREAK, then RESET). The data sheet says unused IVT/AIVT locations should point to a default interrupt handler containing RESET. This is a strong consistency check for the vector-table interpretation.

**Result:** `0x006FA2` is the firmware's I2C1 slave-event ISR entry according to the device's vector definition. This is the best starting point for tracing the PMBus receive/command path. It is not yet proof that the PMBus physical interface is wired to I2C1, nor does it identify any PMBus command handlers.

At `0x006FA2`, the first slots are:

```
PC 0x006FA2  F80036
PC 0x006FA4  BE9F80
PC 0x006FA6  BE9F82
PC 0x006FA8  BE9F84
PC 0x006FAA  BE9F86
PC 0x006FAC  781F88
PC 0x006FAE  801000
PC 0x006FB0  784100
PC 0x006FB2  B7EE5A
PC 0x006FB4  A9C208
PC 0x006FB6  EF6F26
PC 0x006FB8  BFC208
```

These are raw instruction words, not decoded mnemonics. The previous candidate disassembler `dasmxx` supports dsPIC33 but its current decoder table is a limited subset, so it is not sufficient by itself to decode this ISR completely.

## Ghidra processor selection

The current Ghidra PIC processor module contains a dedicated `dsPIC33F.slaspec` language profile. Its language definition identifies it as:

`dsPIC33F:LE:24:default`

Use that profile for this dsPIC33FJ64GS606 target, not dsPIC33E or PIC24H. The source profile includes the shared PIC24/dsPIC instruction specification.

A prepared 4-byte-slot raw program image and a Ghidra annotation script are supplied separately in the analysis bundle. Import the raw image at base address `0x000000`, preserve the 4-byte slots, then disassemble reset, startup and I2C1 ISR entries. Manual review is still required for indirect calls, table-driven branches and peripheral SFR references.

## What is not established yet

1. The exact PMBus slave address configured by this firmware. The user's observed PMBus address `0x58` is separate bench evidence; it is not derived from the vector table.
2. Which I2C1 ISR branches process address match, receive byte, transmit byte, repeated START, STOP, PEC, or command dispatch.
3. Whether the PMBus interface is physically connected to I2C1 or whether another controller/bridge is involved.
4. Whether this `095HR5A00` image is compatible with PCB revision `95HR5A05PS`.
5. Whether the uploaded package contains firmware for one or multiple dsPIC devices.

No live register writes, firmware writes, or flashing operations were performed.

## References

- Microchip dsPIC33FJ32GS406/606/608/610 and dsPIC33FJ64GS406/606/608/610 data sheet DS70591C: https://ww1.microchip.com/downloads/en/DeviceDoc/70591C.pdf
  - Section 4.1: 24-bit program words, reset vector and vector-table address ranges.
  - Section 7.1: each interrupt vector contains a 24-bit ISR start address; SI2C1/MI2C1 and alternate vector table definitions.
- Ghidra PIC processor language definitions: https://github.com/NationalSecurityAgency/ghidra/tree/master/Ghidra/Processors/PIC/data/languages
  - `dsPIC33F.slaspec`, `PIC24.sinc`, and `PIC24.ldefs`.
- dasmxx source (candidate only; its current PIC30 decoder table is incomplete for this ISR): https://github.com/nejohnson/dasmxx
