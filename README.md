# Dell Delta D1600E / 95HR5 PSU reverse engineering

Analysis artifacts for Dell/Delta 1600 W server PSU work, focusing on D1600E-S0 / PCB family 95HR5.

## Firmware artifact analyzed
- Dell payload: `095HR5_190AD_00.3D.67_extracted.bin`
- Package version: `00.3D.67`
- Package PN: `95HR5`
- Internal image label: `095HR5A00`
- Internal token: `000190AD`
- Size: 86,340 bytes
- SHA-256: `eedae0cd8d92e87ca12516c5cebfd80feb23462c424ec25eee10dc5ff40deed0`

**Compatibility warning:** the user's PCB marking is `95HR5A05PS`, while the package identifies `095HR5A00`. This is evidence of the same 95HR5 family, not proof that this image is safe to flash to the A05PS revision.

## Documents
- [Firmware structure analysis](docs/firmware-00.3D.67-analysis.md)
- [PMBus protocol notes](docs/pmbus-protocol-notes.md)

## Status
- [x] Preserve the uploaded payload and compute hashes.
- [x] Verify header MD5.
- [x] Record observed image layout and 4-byte word stride.
- [x] Separate standard PMBus definitions from prior bench observations.
- [ ] Prove image encoding and dsPIC33FJ64GS606 mapping.
- [ ] Disassemble with a verified dsPIC33F backend.
- [ ] Confirm exact hardware-revision compatibility against a read-only dump.
- [ ] Map supported PMBus commands from read-only captures and firmware references.

No firmware has been flashed or modified. No PMBus write commands are recommended at this stage.
