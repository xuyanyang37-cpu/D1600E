#pragma once
#include <stddef.h>
#include <stdint.h>

// D1600E 00.3D.67 固件中提取出的 CRC-8 半字节表。
// 低表对应 CRC8(poly=0x07) 的低半字节输入；高表对应高半字节输入。
// 固件函数候选入口：PC 0x00332A。
// 注意：本文件只实现 CRC-8/0x07 算法；D1600E 实际事务是否把地址/RW/命令/数据全部纳入，
// 以及每笔事务的 CRC 初值重置时机，仍需继续从固件调用路径确认。

static const uint8_t D1600E_CRC8_LO[16] = {
    0x00, 0x07, 0x0E, 0x09, 0x1C, 0x1B, 0x12, 0x15,
    0x38, 0x3F, 0x36, 0x31, 0x24, 0x23, 0x2A, 0x2D
};

static const uint8_t D1600E_CRC8_HI[16] = {
    0x00, 0x70, 0xE0, 0x90, 0xC7, 0xB7, 0x27, 0x57,
    0x89, 0xF9, 0x69, 0x19, 0x4E, 0x3E, 0xAE, 0xDE
};

// 与固件两张半字节表数学等价的单字节更新。
// crc 初值和传入字节顺序由上层事务管理。
static inline uint8_t d1600e_pec_update(uint8_t crc, uint8_t data) {
    uint8_t x = (uint8_t)(crc ^ data);
    return (uint8_t)(D1600E_CRC8_HI[x >> 4] ^ D1600E_CRC8_LO[x & 0x0F]);
}

// 标准 SMBus PEC 计算入口：CRC 初值 0，按收到的字节顺序处理。
// 是否适用于 D1600E 的特定事务，仍要由实际协议流程确认。
static inline uint8_t d1600e_pec_calculate(const uint8_t *data, size_t length) {
    uint8_t crc = 0;
    size_t i;
    for (i = 0; i < length; ++i) {
        crc = d1600e_pec_update(crc, data[i]);
    }
    return crc;
}
