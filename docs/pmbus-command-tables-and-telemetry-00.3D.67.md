# Dell/Delta D1600E 00.3D.67 — PMBus 命令表与遥测路径

## 结论

本轮从程序映像中恢复出两张 PMBus 命令分派表：

1. **读命令表**：程序 PC `0x14D8`，85 组 `命令码 -> 处理函数地址`。
2. **写/事务命令表**：程序 PC `0x18A2`，43 组 `16-bit 描述符 -> 处理函数地址`。描述符低字节与 PMBus 命令码对应，高字节是内部事务/协议描述字段；其全部枚举含义尚未完全恢复。

这两张表直接包含用户实际读取过的 `READ_VOUT 0x8B`、`READ_IOUT 0x8C`、`READ_TEMPERATURE_1..3 0x8D..0x8F`、`READ_FAN_SPEED_1 0x90`，并能定位到具体处理函数。

## 1. 读命令分派表

### 表结构证据

- 程序表起点：PC `0x14D8`。
- PSV 数据指针：`0x94D8`，在 PSVPAG=0 时映射到程序表起点。
- 表项数量：85。
- 每项两个 16-bit word：命令码、处理函数 PC。
- 函数 `0x00280A` 装载 `0x94D8`，循环计数比较值为 `0x55`（85），并调用 `0x00332A` CRC-8 更新例程。它很可能同时用于校验这张命令表的数据完整性。

### 关键读命令

| PMBus 命令 | 命令码 | 固件处理函数 PC |
|---|---:|---:|
| PAGE | 0x00 | 0x1ABE |
| CAPABILITY | 0x19 | 0x1D8A |
| QUERY | 0x1A | 0x1DA8 |
| COEFFICIENTS | 0x30 | 0x2342 |
| FAN_CONFIG_1_2 | 0x3A | 0x1E62 |
| FAN_COMMAND_1 | 0x3B | 0x1E4E |
| STATUS_BYTE | 0x78 | 0x1BC8 |
| STATUS_WORD | 0x79 | 0x1B90 |
| STATUS_VOUT | 0x7A | 0x1BFA |
| STATUS_IOUT | 0x7B | 0x1C2C |
| STATUS_INPUT | 0x7C | 0x1C5E |
| STATUS_TEMPERATURE | 0x7D | 0x1C90 |
| STATUS_CML | 0x7E | 0x1CC2 |
| STATUS_OTHER | 0x7F | 0x1D1A |
| STATUS_FANS_1_2 | 0x81 | 0x1D30 |
| READ_EIN | 0x86 | 0x1D46 |
| READ_EOUT | 0x87 | 0x1D68 |
| READ_VIN | 0x88 | 0x1AC8 |
| READ_IIN | 0x89 | 0x1AE2 |
| READ_VOUT | 0x8B | 0x1AFC |
| READ_IOUT | 0x8C | 0x1B16 |
| READ_TEMPERATURE_1 | 0x8D | 0x1E00 |
| READ_TEMPERATURE_2 | 0x8E | 0x1E1A |
| READ_TEMPERATURE_3 | 0x8F | 0x1E34 |
| READ_FAN_SPEED_1 | 0x90 | 0x1DE0 |
| READ_POUT | 0x96 | 0x1B5C |
| READ_PIN | 0x97 | 0x1B76 |
| PMBUS_REVISION | 0x98 | 0x1D94 |
| APP_PROFILE_SUPPORT | 0x9F | 0x1D9E |
| MFR_POUT_MAX | 0xA7 | 0x21F6 |
| USER_DATA_00..03 | 0xB0..0xB3 | 0x1EBA..0x1EFE |

其余表项包括 0xA0..0xA6、0xD0/0xD2/0xD5/0xD7/0xD8/0xDA/0xDB/0xDC/0xDD/0xDE/0xDF、0xE0..0xE8、0xEB、0xED、0xF0..0xF2 等厂商扩展/设备专用命令。完整 85 项由 `tools/extract_d1600e_pmbus_tables.py` 自动导出。

## 2. 写/事务命令分派表

### 表结构证据

- 程序表起点：PC `0x18A2`。
- PSV 数据指针：`0x98A2`。
- 表项数量：43（循环终止计数 `0x2B`）。
- 每项两个 16-bit word：16-bit 描述符、处理函数 PC。
- `0x00328C` 搜索该表；匹配描述符后进入 `0x00323C` 继续分派。

描述符格式为 `(高字节 << 8) | PMBus命令码`。例如：

- `0x0203`：命令 0x03 CLEAR_FAULTS
- `0x043B`：命令 0x3B FAN_COMMAND_1
- `0x037A`：命令 0x7A STATUS_VOUT
- `0x037B`：命令 0x7B STATUS_IOUT
- `0x05B0`：命令 0xB0 USER_DATA_00
- `0x0605`：命令 0x05 PAGE_PLUS_WRITE

高字节与 SMBus/PMBus 事务类型有关的可能性很高；目前已看到 0x02、0x03、0x04、0x05、0x06、0x08、0x13 等类别，但还不能把所有数值直接等同于 SMBus 标准协议枚举。

### 关键写命令及处理函数

| 描述符 | 命令 | 处理函数 PC |
|---|---|---:|
| 0x0203 | CLEAR_FAULTS 0x03 | 0x2884 |
| 0x043B | FAN_COMMAND_1 0x3B | 0x2886 |
| 0x037A..0x037F | STATUS_VOUT..STATUS_OTHER | 0x2CAC..0x2E26 |
| 0x0381 | STATUS_FANS_1_2 0x81 | 0x2E44 |
| 0x05B0/0x13B1/0x05B2/0x13B3 | USER_DATA_00..03 | 0x29BC/0x29C0/0x29EE/0x2A02 |
| 0x0605 | PAGE_PLUS_WRITE 0x05 | 0x2B30 |
| 0x041B | SMBALERT_MASK 0x1B | 0x2BCE |
| 0x0440 | VOUT_OV_FAULT_LIMIT 0x40 | 0x28D4 |
| 0x0444 | VOUT_UV_FAULT_LIMIT 0x44 | 0x28F8 |
| 0x0446 | IOUT_OC_FAULT_LIMIT 0x46 | 0x291C |
| 0x044A | IOUT_OC_WARN_LIMIT 0x4A | 0x295E |
| 0x045D | IIN_OC_WARN_LIMIT 0x5D | 0x2C2E |
| 0x046B | PIN_OP_WARN_LIMIT 0x6B | 0x2C6C |
| 0x0300 | PAGE 0x00 | 0x286C |
| 0x0630 | COEFFICIENTS 0x30 | 0x2CAA |

厂商扩展命令 E1/E2/E3 也在写表中：
- E1：描述符 `0x04E1`，处理函数 `0x2E92`
- E2：描述符 `0x04E2`，处理函数 `0x2EC6`
- E3：描述符 `0x04E3`，处理函数 `0x2EFE`

对应读表处理函数分别为 E1 `0x2308`、E2 `0x2316`、E3 `0x2324`。命令已确认存在，但具体物理意义仍需反向追踪，不能仅凭 E1/E2/E3 编号推断功能。

## 3. PAGE 与遥测数据路径

**地址口径说明：**以下 `0x072E`、`0x0755` 等是 dsPIC `f15b` 指令中的 word-address 字段，不是数据空间字节地址。Ghidra PIC24/dsPIC33F 语言定义明确对 `f15b` 地址左移 1 位，因此实际数据空间字节地址为字段值 × 2。相反，`f13` 直接文件寄存器地址不做这个左移。

多个读命令处理函数首先读取 `f15b=0x072E`（实际数据空间字节地址 `0x0E5C`），并与 `0x00FF` 比较。这是当前 PAGE 选择变量的强证据。

PAGE=0xFF 与 PAGE 非 0xFF 时，处理函数会选择不同的遥测数据地址：

| 命令 | PAGE=0xFF f15b 字段（实际字节地址） | PAGE 非 0xFF f15b 字段（实际字节地址） | 处理函数 |
|---|---:|---:|---:|
| READ_VIN 0x88 | 0x0752（0x0EA4） | 0x0780（0x0F00） | 0x1AC8 |
| READ_IIN 0x89 | 0x0753（0x0EA6） | 0x0781（0x0F02） | 0x1AE2 |
| READ_VOUT 0x8B | 0x0755（0x0EAA） | 0x0783（0x0F06） | 0x1AFC |
| READ_IOUT 0x8C | 0x0756（0x0EAC） | 0x0784（0x0F08） | 0x1B16 |
| READ_TEMP_1 0x8D | 0x0759（0x0EB2） | 0x0787（0x0F0E） | 0x1E00 |
| READ_TEMP_2 0x8E | 0x0758（0x0EB0） | 0x0786（0x0F0C） | 0x1E1A |
| READ_TEMP_3 0x8F | 0x075A（0x0EB4） | 0x0788（0x0F10） | 0x1E34 |
| READ_FAN_SPEED_1 0x90 | 特殊计算路径 | 0x0789（0x0F12） | 0x1DE0 |

READ_VOUT 的处理代码 `0x1AFC`：
1. 读取 PAGE 变量 `0x072E`；
2. PAGE=0xFF 时读取 `0x0755`，否则读取 `0x0783`；
3. 将 16-bit 数据拆成两个字节写入响应缓冲区 `0x0E0F/0x0E10`；
4. 将响应长度写为 2（变量 `0x0E57`）。

READ_IOUT 和温度读函数采用相似的两字节返回框架。这里的读处理函数直接取已计算的 RAM 值，不代表物理单位或 Linear 格式已在读函数内转换；单位转换发生在上游采样/计算路径。

### 遥测变量的上游写入线索

- `0x0755`（READ_VOUT PAGE=0xFF 值）在 `0x0070E2` 写入。
- `0x0756`（READ_IOUT PAGE=0xFF 值）在 `0x0070BC` 写入；该路径调用 `0x0033D6`，参数包含指数种子 `-7` 和比例参数 `100`。
- `0x0752`、`0x0753` 在 `0x005300)、`0x00531E` 写入；这些路径也调用 `0x0033D6`。
- 温度变量 `0x0758/0x0759/0x075A` 在 `0x006770) 附近更新。

`0x0033D6` 有 11-bit mantissa 掩码和指数归一化/打包逻辑，形态符合 PMBus LINEAR11 转换器；下一步应继续验证每个调用点的指数、缩放和最终编码，不应将所有读数统一按 ULINEAR16 解释。

## 4. 风扇转速：IC1 输入捕获到 READ_FAN_SPEED_1

### 硬件路径证据

- IC1 中断向量目标：`PC=0x005F0A`。
- `0x005F1E` 读取 `IC1CON`（SFR `0x0142`）。
- `0x005F20` 测试 bit 3；dsPIC33FJ64GS606 数据手册中该位是 `ICBNE`（Input Capture Buffer Not Empty）。
- 紧接着的 `0x800A00` 是 `f15b=0x00A0` 的字地址访问，实际数据空间字节地址为 `0x0140`，正好对应 IC1BUF。
- 捕获时间值被保存到 `f15b=0x0A0F/0x0A11`（实际数据空间字节地址 `0x141E/0x1422`）。
- `0x005F44` 使用这两个捕获值计算周期；若周期非零，装载 32-bit 常量 `0x011E1A30`，调用 `0x001028` 的 32-bit 除法例程。该计算形态符合由输入捕获周期换算风扇转速，但 timer 时钟和每转脉冲数仍需结合初始化参数确认。

### PMBus 输出路径

`READ_FAN_SPEED_1`（命令 0x90，处理函数 `0x1DE0`）：
- PAGE=0xFF：调用 `0x005F44` 计算转速，再调用 `0x0033D6`（参数 W2=4、W1=1）转换成 PMBus 数值格式；
- PAGE 非 0xFF：直接读取 RAM `0x0789`；
- 最后将 16-bit 结果写入 `0x0E0F/0x0E10)，响应长度为 2。

这意味着 READ_FAN_SPEED_1 并不是简单读取一个固定 RAM 值；PAGE=0xFF 路径实际依赖 IC1 捕获的风扇转速。

## 5. FAN_COMMAND_1 控制路径

- 读命令表：`0x3B -> 0x1E4E`。处理函数读取 `f15b=0x0733`（实际数据空间字节地址 `0x0E66`），再调用 `0x0033D6` 形成 16-bit 响应。
- 写/事务表：`0x043B -> 0x2886`。处理函数从 I2C/PMBus 数据缓冲区 `0x0E34` 取输入数据，执行范围/比例计算，并写入 `f15b=0x0732/0x0733`（实际字节地址 `0x0E64/0x0E66`）。
- 主控制路径 `0x006140` 附近读取 `f15b=0x0732`（实际字节地址 `0x0E64`），并与 `f15b=0x0A17`（实际字节地址 `0x142E`）比较/更新，说明 PMBus FAN_COMMAND_1 写入值进入风扇控制状态变量。
- 同一控制路径调用 `0x006030`；该函数在 `PC=0x006044` 执行 `882330`。按 dsPIC `f15b` 地址编码换算，其有效数据空间地址为 `0x0466)，对应 dsPIC33FJ64GS606 的高速度 PWM Generator 3 的 `PDC3` 占空比寄存器。其他动态写入点包括 `0x005EE4`、`0x0060A6`、`0x006116`、`0x006246`。

因此，PMBus FAN_COMMAND_1 已经能追到后续控制状态，而且控制代码动态写入 PWM3 的 PDC3。**这强烈表明 PWM3 是风扇控制输出路径的一部分**；实际板上对应哪个引脚、PWM3 是否直接驱动风扇 MOSFET/缓冲器，还需要结合 dsPIC 引脚复用配置和 PCB 走线确认。

## 6. 与用户实测命令的对应关系

- `READ_VOUT 0x8B`、`READ_IOUT 0x8C)、`READ_TEMP_1..3 0x8D..0x8F)、`READ_FAN_SPEED_1 0x90) 均在读命令表中有明确处理函数。
- `STATUS_WORD 0x79)、`STATUS_CML 0x7E) 也有明确处理函数。
- `VOUT_MODE 0x20)、`VOUT_COMMAND 0x21)、`VOUT_MAX 0x24) 没有出现在当前恢复出的 85 项读表和 43 项写/事务表中。这与用户实测读回 `0xFF/0xFFFF` 的现象相符，提示这些命令可能未实现或走默认异常响应；仍需检查通用 fallback 路径后才能定论。
- 厂商命令 E1/E2/E3 已确认存在于读表和写表；具体语义尚未确认。

## 7. 下一步

1. 继续追踪 `0x0033D6`，确认 LINEAR11 打包规则和不同测量通道的指数/比例。
2. 追踪 `0x006140`、`0x006676)、`0x0066B8) 以及 FAN_COMMAND_1 写入的 `0x0732/0x0733)，确认风扇控制最终输出端。
3. 反向分析厂商命令 E1/E2/E3 的读写处理函数，解释用户之前看到的变化。
4. 追踪 I2C1 CRC-8 状态初始化、地址字节覆盖、PEC 接收比较和发送追加，最终确认是否完整实现 SMBus PEC。
5. 搜索并验证 READ_VOUT/READ_IOUT 上游 ADC 原始采样、比例常数和物理单位。

## 8. 安全边界

本报告为离线固件静态分析。表中存在命令处理函数，不代表这些命令可以安全写入任意值。特别是 E1/E2/E3 和 FAN_COMMAND_1，在参数范围、默认状态及硬件输出关系完全确认前，不建议向电源发送试写命令。
