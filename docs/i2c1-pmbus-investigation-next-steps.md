# D1600E 00.3D.67 – I2C1/PMBus firmware investigation notes

Date: 2026-11-14

## Scope

This note extends the vector analysis for the extracted Dell payload `095HR5_190AD_00.3D.67_extracted(1).bin`. It uses the previously recorded binary observations plus Microchip's device datasheet and I2C family reference manual. It does **not** claim a new disassembly of the binary ISR: the current data-analysis runtime is unavailable, so the raw payload could not be re-read or instruction-decoded in this session.

## 1. Firmware vector evidence

Previously recorded from the payload:
- SI2C1 vector at program PC `0x000034` contains `0x006FA2`.
- The AIVT SI2C1 slot at PC `0x000134` also contains `0x006FA2`.
- The device data sheet maps vector address `0x000034` to SI2C1 (I2C1 Slave Event), and `0x000134` to the alternate SI2C1 vector.

**Working conclusion:** `0x006FA2` is the I2C1 slave-event ISR entry in this firmware, assuming the extracted program-record-to-PC mapping already documented is correct. It is not yet a decoded PMBus command handler.

## 2. Device-specific I2C1 register map

For dsPIC33FJ64GS606, the data sheet's SFR map lists:

| Register | SFR address | Relevant role |
|---|---:|---|
| I2C1RCV | `0x0200` | Receive byte; reading clears RBF |
| I2C1TRN | `0x0202` | Transmit byte |
| I2C1BRG | `0x0204` | I2C baud-rate generator |
| I2C1CON | `0x0206` | I2C enable, SMBus threshold, clock release, ACK control |
| I2C1STAT | `0x0208` | R/W, D/A, Start/Stop, RBF, overflow, collision status |
| I2C1ADD | `0x020A` | 7-/10-bit slave address |
| I2C1MSK | `0x020C` | Address mask |

The I2C1CON bit list includes I2CEN, I2CSIDL, SCLREL, IPMIEN, A10M, DISSLW, SMEN, GCEN and STREN, plus ACK/receive/master control bits. Do not assume every optional bit described in the generic family manual exists on this specific device. In particular, AHEN/DHEN are discussed by the generic manual as PMBus-related acknowledgement-hold features, but they are not listed in this device's I2C1CON register map. Verify the actual device register definitions before assuming the firmware uses them.

## 3. Status bits that should identify ISR branches

I2C1STAT is at SFR address `0x0208`. The device data sheet identifies:
- bit 6: I2COV – receive overflow
- bit 5: D_A – data/address indication
- bit 4: P – Stop condition detected
- bit 3: S – Start condition detected
- bit 2: R_W – direction of transfer
- bit 1: RBF – receive buffer full
- bit 0: TBF – transmit buffer full
- bit 15: ACKSTAT – acknowledge status (primarily master-side context)
- bit 14: TRSTAT – transmit status
- bit 7: IWCOL – write collision

The I2C family reference manual explains that the SI2CxIF slave interrupt can be generated for Start, Stop, Repeated Start, valid address match, a transmit request/termination, and data reception. Therefore, an ISR may be a state/event dispatcher, not simply a byte receive routine.

For slave reception:
- A matching address is recognized by hardware.
- For a master write, R/W is cleared; the slave receives command/data bytes.
- Received data sets RBF and D/A; firmware must read I2C1RCV to consume the byte and clear RBF.
- A stale RBF can cause receive overflow (I2COV), and hardware may NACK subsequent bytes.
- For master read, R/W is set; the firmware must load the next reply byte into I2C1TRN.

These hardware facts give a reliable checklist for identifying code around ISR `0x006FA2`.

## 4. Address interpretation: observed 0x58

The generic I2C reference manual states that in 7-bit mode I2CxADD<6:0> stores the 7-bit slave address; the R/W bit is not part of I2CxADD.

If the user's observed `0x58` is the 7-bit PMBus address, then:
- I2C1ADD should contain `0x58` (subject to address mask/configuration).
- Address byte on the bus for write is `0xB0`.
- Address byte on the bus for read is `0xB1`.

This is a format conversion only. It does not independently prove that this firmware sets I2C1ADD to 0x58. The value must be located in the startup/configuration code or confirmed from a safe bus capture.

## 5. SMBus / PMBus implications

The dsPIC33FJ64GS606 data sheet describes two I2C modules with SMBus support. I2C1CON includes SMEN for SMBus input thresholds. The I2C hardware itself handles bus-level address recognition, byte shifting, ACK/NACK and status flags. PMBus command semantics, multi-byte command payloads, PEC CRC-8, telemetry conversion, and vendor command dispatch still require firmware/software handling unless explicitly supported by a peripheral feature.

The generic family manual specifically notes that AHEN/DHEN provide extra address/data acknowledgement interrupts and clock stretching to support PMBus on device variants that implement them. Since the device-specific I2C1CON register map does not list these bits, do not assume this exact MCU variant uses that mechanism.

## 6. Exact next checks in a real dsPIC33F disassembly

At ISR entry `0x006FA2`, inspect these in order:

1. **Context save/restore:** identify W-register pushes/pops and any shadow-register use.
2. **Interrupt flag handling:** locate clearing of SI2C1IF (IFS1 bit 0 on this device).
3. **Status sampling:** locate reads of I2C1STAT (`0x0208`).
4. **Receive path:** locate reads of I2C1RCV (`0x0200`) and stores into RAM; determine whether the first received byte is treated as the PMBus command code.
5. **Transmit path:** locate writes to I2C1TRN (`0x0202`) and the state/command lookup that chooses reply bytes.
6. **Start/Stop/repeated-start:** determine whether S/P flags reset the command index or transaction state.
7. **Overflow/error handling:** identify I2COV, IWCOL, ACK/NACK and buffer-state handling.
8. **PEC:** find CRC-8 update logic and check whether the address+R/W byte, command code and data bytes are included as required by PMBus transaction type.
9. **Command table:** cross-reference command bytes with READ_VOUT (0x8B), READ_IOUT (0x8C), READ_TEMPERATURE_1 (0x8D), READ_FAN_SPEED_1 (0x90), STATUS_WORD (0x79), and vendor command ranges. These command codes are search targets, not proof that all are implemented.

### Likely SFR cross-reference signatures

Search the disassembly's data-space references for these exact SFR addresses (check Ghidra's data-space address mapping; these are not program-memory addresses):

```
0x0200  I2C1RCV
0x0202  I2C1TRN
0x0204  I2C1BRG
0x0206  I2C1CON
0x0208  I2C1STAT
0x020A  I2C1ADD
0x020C  I2C1MSK
```

Do not confuse the program-space vector PC `0x0034` with the data-space I2C1 SFR addresses above.

## 7. Safety and confidence boundaries

- No PSU register writes, MCU writes, or firmware flashing were performed.
- User bench evidence for PMBus address `0x58` remains separate from the firmware evidence.
- Firmware header model `095HR5A00` versus user's PCB marking `95HR5A05PS` remains an unresolved compatibility issue.
- The current note identifies what the I2C1 ISR must be checked for; it does not yet claim a complete ISR disassembly, PMBus command map, PEC implementation, or exact I2C1ADD value.

## References

1. Microchip, dsPIC33FJ32GS406/606/608/610 and dsPIC33FJ64GS406/606/608/610 Data Sheet, DS7000591F: https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ProductDocuments/DataSheets/70000591f.pdf
   - Table 7-1: SI2C1/MI2C1 interrupt vector addresses.
   - I2C1 SFR register map: I2C1RCV through I2C1MSK and I2C1CON/I2C1STAT bit fields.
2. Microchip, dsPIC33/PIC24 Family Reference Manual, Inter-Integrated Circuit (I2C), DS70000195F: https://ww1.microchip.com/downloads/en/devicedoc/70000195f.pdf
   - Section 7.3: address detection.
   - Section 7.4: slave receive and RBF/I2COV behavior.
   - Section 7.5: slave transmit behavior.
   - SI2CxIF event list and PMBus-related AHEN/DHEN discussion.


## 8. Partial instruction decode at the ISR entry

The raw instruction words previously recorded at `0x006FA2` can now be partially decoded against Microchip's dsPIC33F instruction encodings:

| PC | Word | Decoded instruction | Confidence |
|---|---:|---|---|
| `0x006FA2` | `F80036` | `PUSH 0x0036` = `PUSH RCOUNT` | High |
| `0x006FA4` | `BE9F80` | `MOV.D W0, [W15++]` | High |
| `0x006FA6` | `BE9F82` | `MOV.D W2, [W15++]` | High |
| `0x006FA8` | `BE9F84` | `MOV.D W4, [W15++]` | High |
| `0x006FAA` | `BE9F86` | `MOV.D W6, [W15++]` | High |
| `0x006FAC` | `781F88` | `MOV W8, [W15++]` | High (matching dsPIC33 disassembly example) |
| `0x006FAE` | `801000` | Not yet independently verified | Open |
| `0x006FB0` | `784100` | Not yet independently verified | Open |

The first six instructions are a compiler-style ISR prologue: it preserves RCOUNT and W0–W8 (W0/W1, W2/W3, W4/W5, W6/W7 as double words, plus W8) on the stack. This is register preservation, not evidence of PMBus command handling by itself. The next instruction words must be decoded before interpreting the ISR body.

Microchip's Programmer's Reference Manual defines the PUSH file-register encoding as `1111 1000 ffff ffff ffff fff0`; with `f=0x0036`, `F80036` is `PUSH 0x0036`. The device data/core register map places RCOUNT at data-space address `0x0036`. The manual also defines `MOV.D Wns,[W15++]` as a double-word push-equivalent operation. A published dsPIC33 disassembly example independently shows `F80036` as `PUSH RCOUNT`, `BE9F80` as `MOV.D W0,[W15++]`, and `781F88` as `MOV W8,[W15++]`.

This partial decode increases confidence that `0x006FA2` is a genuine code entry and that the four-byte-slot extraction was interpreted with the correct instruction alignment. It does **not** yet identify the I2C status tests, RCV/TRN accesses, PEC routine, or command dispatch.

Reference:
- Microchip 16-Bit MCU and DSC Programmer's Reference Manual DS70000157G: https://ww1.microchip.com/downloads/en/DeviceDoc/70000157g.pdf
  - PUSH f encoding and MOV.D descriptions.
- dsPIC33F assembly example with matching prologue opcodes: https://www.todopic.com.ar/foros/index.php?topic=45240.0
