#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "d1600e_pec_crc8.h"

static uint8_t crc8_bitwise_reference(const uint8_t *data, size_t length) {
    uint8_t crc = 0;
    size_t i;
    uint8_t bit;
    for (i = 0; i < length; ++i) {
        crc ^= data[i];
        for (bit = 0; bit < 8; ++bit) {
            crc = (crc & 0x80)
                ? (uint8_t)((crc << 1) ^ 0x07)
                : (uint8_t)(crc << 1);
        }
    }
    return crc;
}

int main(void) {
    static const uint8_t check[] = "123456789";
    uint8_t table_crc = d1600e_pec_calculate(check, 9);
    uint8_t bitwise_crc = crc8_bitwise_reference(check, 9);

    // CRC-8/SMBus polynomial 0x07, init 0, check value for ASCII "123456789".
    assert(table_crc == 0xF4);
    assert(table_crc == bitwise_crc);

    printf("CRC8 table result: 0x%02X\n", table_crc);
    printf("CRC8 bitwise result: 0x%02X\n", bitwise_crc);
    return 0;
}
