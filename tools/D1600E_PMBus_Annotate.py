# Ghidra annotations for Dell D1600E 00.3D.67 PMBus/PEC analysis
# Import the 4-byte-per-program-word image with dsPIC33F:LE:24:default at base 0.

def label(addr, name, comment=None):
    a = toAddr(addr)
    createLabel(a, name, True)
    if comment:
        setPlateComment(a, comment)

def func(addr, name, comment=None):
    a = toAddr(addr)
    label(addr, name, comment)
    disassemble(a)
    try:
        createFunction(a, name)
    except:
        pass

label(0x000C62, "PSV_INIT_DISABLE", "BCLR CORCON.PSV before configuring page.")
label(0x000C6C, "PSVPAG_ZERO", "MOV W0=0 to PSVPAG.")
label(0x000C6E, "PSV_INIT_ENABLE", "BSET CORCON.PSV.")
label(0x0014D8, "PMBUS_COMMAND_HANDLER_TABLE",
      "85 pairs: 16-bit PMBus command code followed by 16-bit handler PC.")
label(0x001882, "SMBUS_CRC8_POLY07_LOW_NIBBLE_TABLE",
      "16-byte nibble table: 00 07 0E 09 1C 1B 12 15 38 3F 36 31 24 23 2A 2D.")
label(0x001892, "SMBUS_CRC8_POLY07_HIGH_NIBBLE_TABLE",
      "16-byte nibble table: 00 70 E0 90 C7 B7 27 57 89 F9 69 19 4E 3E AE DE.")

func(0x00280A, "I2C1_READ_COMMAND_DISPATCH",
     "Loads PSV command table base 0x94D8 and dispatches through indirect CALL W0.")
func(0x00332A, "SMBUS_PEC_CRC8_UPDATE",
     "Uses RAM state 0x13F0 and PSV lookup tables at data addresses 0x9882/0x9892.")
func(0x003B94, "MFR_E1_READ_HELPER",
     "Reads internal RAM 0x13AA; called by command 0xE1 handler.")
func(0x003B4E, "MFR_E3_READ_HELPER",
     "Reads internal RAM 0x1398; called by command 0xE3 handler.")

func(0x001AFC, "PMBUS_READ_VOUT_8B",
     "Two-byte response sourced from RAM 0x0EAA or 0x0F06 depending on selector 0x0E5C.")
func(0x001B16, "PMBUS_READ_IOUT_8C",
     "Two-byte response sourced from RAM 0x0EAC or 0x0F08.")
func(0x001E00, "PMBUS_READ_TEMPERATURE_1_8D")
func(0x001E1A, "PMBUS_READ_TEMPERATURE_2_8E")
func(0x001E34, "PMBUS_READ_TEMPERATURE_3_8F")
func(0x001DE0, "PMBUS_READ_FAN_SPEED_1_90")
func(0x001B5C, "PMBUS_READ_POUT_96")
func(0x001B76, "PMBUS_READ_PIN_97")

func(0x001BC8, "PMBUS_STATUS_BYTE_78")
func(0x001B90, "PMBUS_STATUS_WORD_79")
func(0x001BFA, "PMBUS_STATUS_VOUT_7A")
func(0x001C2C, "PMBUS_STATUS_IOUT_7B")
func(0x001C5E, "PMBUS_STATUS_INPUT_7C")
func(0x001C90, "PMBUS_STATUS_TEMPERATURE_7D")
func(0x001CC2, "PMBUS_STATUS_CML_7E")
func(0x001D1A, "PMBUS_STATUS_OTHER_7F")

func(0x002308, "PMBUS_MFR_E1_HANDLER",
     "Read-side handler returns two bytes; helper 0x3B94 reads RAM 0x13AA.")
func(0x002324, "PMBUS_MFR_E3_HANDLER",
     "Read-side handler calls 0x3B4E and 0x33D6; returns two bytes.")

func(0x006F56, "I2C1_SET_OWN_ADDRESS_58",
     "MOV #0x58,W0; MOV W0,I2C1ADD at 0x020A; RETURN.")
func(0x006F6A, "I2C1_TRANSMIT_HELPER",
     "Nearby code writes W0/W1 to I2C1TRN at 0x0202.")
func(0x006FA2, "I2C1_SLAVE_EVENT_ISR",
     "SI2C1 vector at PC 0x0034 and AIVT PC 0x0134.")
