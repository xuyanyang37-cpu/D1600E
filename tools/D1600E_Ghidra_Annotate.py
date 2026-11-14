# Ghidra Script: initial annotations for Dell D1600E 00.3D.67 dsPIC33F image
# Import raw image with language dsPIC33F:LE:24:default at base address 0.
# Keep 4-byte instruction slots intact.

def annotate(addr, name, comment=None):
    a = toAddr(addr)
    createLabel(a, name, True)
    if comment:
        setPlateComment(a, comment)

def make_func(addr, name):
    a = toAddr(addr)
    disassemble(a)
    try:
        createFunction(a, name)
    except:
        pass

annotate(0x000000, "RESET_VECTOR_GOTO",
         "Observed GOTO 0x000C00; second slot at PC 0x000002.")
annotate(0x000C00, "RESET_STAGE1",
         "Observed GOTO 0x000C40; second slot at PC 0x000C02.")
annotate(0x000C40, "STARTUP_ENTRY",
         "Candidate startup entry reached by reset chain.")

annotate(0x000034, "IVT_SI2C1_VECTOR",
         "Vector value 0x006FA2: I2C1 Slave Event ISR.")
annotate(0x000134, "AIVT_SI2C1_VECTOR",
         "Alternate vector also points to 0x006FA2.")
annotate(0x000036, "IVT_MI2C1_VECTOR",
         "Firmware vector value 0x001018 (default handler).")
annotate(0x000076, "IVT_SI2C2_VECTOR",
         "Firmware vector value 0x001018 (default handler).")
annotate(0x000078, "IVT_MI2C2_VECTOR",
         "Firmware vector value 0x001018 (default handler).")
annotate(0x001018, "DEFAULT_INTERRUPT_HANDLER",
         "Starts 0xDA4000 (BREAK), then 0xFE0000 (RESET).")
annotate(0x006FA2, "I2C1_SLAVE_EVENT_ISR",
         "Resolved from dsPIC33F SI2C1 vector at PC 0x0034.")

entries = [
    (0x003E06, "ISR_INT0"),
    (0x005F0A, "ISR_IC1"),
    (0x007BB4, "ISR_T1"),
    (0x00778A, "ISR_T2"),
    (0x005EEC, "ISR_T3"),
    (0x006F3C, "ISR_T5"),
    (0x005594, "ISR_U2RX"),
    (0x007404, "ISR_ADC_PAIR0"),
    (0x00740A, "ISR_ADC_PAIR1"),
    (0x0072C2, "ISR_ADC_PAIR7"),
]
for addr, name in entries:
    annotate(addr, name)

for addr, name in [
    (0x000000, "RESET_VECTOR_GOTO"),
    (0x000C00, "RESET_STAGE1"),
    (0x000C40, "STARTUP_ENTRY"),
    (0x001018, "DEFAULT_INTERRUPT_HANDLER"),
    (0x003E06, "ISR_INT0"),
    (0x005F0A, "ISR_IC1"),
    (0x007BB4, "ISR_T1"),
    (0x00778A, "ISR_T2"),
    (0x005EEC, "ISR_T3"),
    (0x006FA2, "I2C1_SLAVE_EVENT_ISR"),
    (0x006F3C, "ISR_T5"),
    (0x005594, "ISR_U2RX"),
    (0x007404, "ISR_ADC_PAIR0"),
    (0x00740A, "ISR_ADC_PAIR1"),
    (0x0072C2, "ISR_ADC_PAIR7"),
]:
    make_func(addr, name)

print("Initial labels/comments applied. Review disassembly and indirect control flow manually.")
