# D1600E 00.3D.67：程序区布局与中断覆盖分析（阶段性）

## 分析对象与复核方法

对象：用户上传的 `095HR5_190AD_00.3D.67_extracted(1).bin`。

- 文件大小：86,340 bytes（0x15144）
- SHA-256：`eedae0cd8d92e87ca12516c5cebfd80feb23462c424ec25eee10dc5ff40deed0`
- 固件版本字段：`00.3D.67`
- 固件头型号字段：`095HR5A00`
- 内部 ID 字段：`000190AD`
- 程序记录区偏移：`0x144`
- 记录数：21,504
- 每条记录：3 字节 little-endian 24-bit 内容 + 1 个 0x00 填充字节

本报告对原始二进制重新统计，不依赖先前被截断显示的 CSV 预览。程序记录的 PC 候选映射为 record_index × 2；每条记录在文件中占 4 字节。

## 1. Ghidra 代码空间格式已得到上游定义支持

Ghidra 官方 PIC 处理器模块中的 `PIC24.sinc` 定义：
- `define endian=little`
- ROM 空间为 24-bit、wordsize=2
- 每条 canonical instruction 占 4 个文件字节，其中第 4 字节为 padding
- `dsPIC33F.slaspec` 引入该 PIC24/dsPIC 指令定义

因此，此固件的 4-byte slot 布局与 Ghidra dsPIC33F 处理器模块的存储模型相符；导入时应保留第四个 padding byte，不应把整个文件压缩成连续 3-byte 指令流。

参考：
- https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/Processors/PIC/data/languages/dsPIC33F.slaspec
- https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/Processors/PIC/data/languages/PIC24.sinc

## 2. 非擦除记录分布

以 24-bit 值不等于 `0xFFFFFF` 作为非擦除记录判据，得到：

| 记录索引 | PC 范围 | 数量 | 观察 |
|---|---:|---:|---|
| 0–127 | 0x000000–0x0000FE | 128 | 主 IVT / 复位向量区域 |
| 130–255 | 0x000104–0x0001FE | 126 | AIVT 区域（0x100、0x102 两条为擦除值） |
| 1536–1561 | 0x000C00–0x000C32 | 26 | 两字 GOTO 序列区 |
| 1568–16159 | 0x000C40–0x007E3E | 14,592 | 连续非擦除程序区 |
| 21502–21503 | 0x00A7FC–0x00A7FE | 2 | 尾部非擦除记录，意义待确认 |

0x000C40–0x007E3E 是当前文件中最长的连续非擦除区域。0x007E40 至 0x00A7FA 区域记录为 0xFFFFFF 填充值；最后两条为 0x00ABCD、0xF162C0。尚未确认尾部两条记录是否属于配置字、校验字或其他元数据。

## 3. 复位链与 0xC00 附近的 GOTO 序列

已确认的两字 GOTO：
- PC 0x000000：0x040C00 + 0x000000，跳转目标 0x000C00
- PC 0x000C00：0x040C40 + 0x000000，跳转目标 0x000C40

因此复位路径为：`0x000000 → 0x000C00 → 0x000C40`。

PC 0x000C04–0x000C32 还有 12 组两字 GOTO，其目标依次为：

| GOTO 起始 PC | 目标 PC |
|---|---:|
| 0x000C04 | 0x0072C2 |
| 0x000C08 | 0x007404 |
| 0x000C0C | 0x006F3C |
| 0x000C10 | 0x005EEC |
| 0x000C14 | 0x005F0A |
| 0x000C18 | 0x00778A |
| 0x000C1C | 0x006FA2 |
| 0x000C20 | 0x007BB4 |
| 0x000C24 | 0x003E06 |
| 0x000C28 | 0x0190AD |
| 0x000C2C | 0x005594 |
| 0x000C30 | 0x00740A |

其中除 0x0190AD 外，其余目标与主 IVT/AIVT 中识别出的非默认中断入口一一对应。这说明该区域很可能是与中断入口有关的 GOTO trampoline/跳转序列，但目前没有发现指向该序列的向量引用，故暂不把它定性为“中断分发表”。0x0190AD 超出本固件记录覆盖的程序地址范围，属于待解释异常目标；不能把它直接当作有效 ISR 地址。

## 4. 主 IVT/AIVT 中的非默认入口

按 DS70591C 中 dsPIC33FJ64GS606 中断向量表，将固件向量值对应如下：

| IVT PC | 中断源 | 固件目标 |
|---:|---|---:|
| 0x0014 | INT0 | 0x003E06 |
| 0x0016 | IC1 | 0x005F0A |
| 0x001A | T1 | 0x007BB4 |
| 0x0022 | T2 | 0x00778A |
| 0x0024 | T3 | 0x005EEC |
| 0x0034 | SI2C1 | 0x006FA2 |
| 0x004C | T5 | 0x006F3C |
| 0x0050 | U2RX | 0x005594 |
| 0x00F0 | ADC Pair 0 | 0x007404 |
| 0x00F2 | ADC Pair 1 | 0x00740A |
| 0x00FE | ADC Pair 7 | 0x0072C2 |

对应的 AIVT 入口（IVT PC + 0x100）具有相同目标值。未列出的已实现向量多指向默认处理程序 0x001018。

### 关键解释

- SI2C1 向量指向 0x006FA2，证明固件为 I²C1 从机事件安装了专用 ISR。
- I²C1 主机事件 MI2C1（PC 0x0036）、I²C2 从机/主机事件（PC 0x0076/0x0078）指向默认处理程序。
- ADC Pair 0、1、7 有专用入口；其他 ADC Pair 向量指向默认处理程序。
- PWM1–PWM9 中断向量（0x00D0–0x00E0）指向默认处理程序；PSEM 向量 0x0086、0x00A6 也指向默认处理程序。这只能说明这些向量没有独立 ISR，不能据此推断 PWM 硬件未使用。
- UART2 RX 有专用 ISR；UART2 TX 与 UART2 Error 向量指向默认处理程序。

数据手册还明确指出：未使用的 IVT/AIVT 位置应指向包含 RESET 指令的默认中断处理程序。固件在 PC 0x001018 处以 `0xDA4000`、`0xFE0000` 开始，与这一约定一致。

## 5. 当前可以提出的系统结构假设

已直接观察到：
1. I²C1 从机事件 ISR；
2. 三个 ADC Pair 专用中断入口；
3. Timer1/2/3/5、Input Capture 1、INT0 和 UART2 RX 专用入口。

这组外设组合与“dsPIC 负责数字监控、采样、通信和事件处理”的方案相容。但目前尚未从主循环和 SFR 写入点证明：
- ADC Pair 0/1/7 分别连接输出电压、电流、温度中的哪一路；
- PWM 模块是否被配置、是否参与功率级控制；
- UCC28950 的 COMP/EA/FB 是否受 dsPIC 通过 DAC、PWM 滤波或 GPIO 影响；
- UART2 是否连接另一颗 MCU；
- I²C1 是否就是外部 PMBus 接口。

因此，现阶段不能确认 dsPIC 只做监控，也不能确认它直接闭环控制电源。

## 6. 下一步静态分析清单

1. 以 Ghidra 的 `dsPIC33F:LE:24:default` 导入完整 4-byte slot image，验证 0xC40、0x6FA2、0x7404、0x740A、0x72C2、0x5594、0x7BB4 等入口的指令解码。
2. 对 0x6FA2 ISR 建立完整控制流图，找 I2C1STAT/RCV/TRN 访问、缓冲区读写、状态分支和调用点。
3. 对 0x7404/0x740A/0x72C2 ADC ISR 追踪 ADCBUF/ADSTAT 访问及结果存储位置。
4. 对 0x5594 UART2 RX ISR 追踪 U2RXREG 访问和接收缓冲区。
5. 对 Timer/IC1 ISR 追踪计数器、周期变量和捕获值，判断是否用于风扇转速或调度。
6. 从启动函数追踪时钟、GPIO、I2C1、ADC、PWM、UART2 的初始化 SFR 写入。
7. 对 0x0190AD 和尾部 0x00ABCD/0xF162C0 单独查证，暂不赋予功能含义。

## 7. 风险与边界

- 用户 PCB 丝印为 95HR5A05PS；固件头型号为 095HR5A00。兼容性没有被证明，禁止仅凭本报告刷写。
- 用户实测 PMBus 地址 0x58 是独立台架证据，不是本次固件向量分析推导出的结果。
- 本报告只做静态只读分析；没有写入 PMBus 寄存器、修改固件或刷写电源。
- 任何尚未经过 Ghidra/XC16 实际反汇编验证的指令助记符，都不在本报告中作为结论引用。

## References

- Microchip DS70591C: https://ww1.microchip.com/downloads/en/DeviceDoc/70591C.pdf
- Microchip DS70204C CPU reference manual: https://ww1.microchip.com/downloads/aemDocuments/documents/OTH/ProductDocuments/ReferenceManuals/70204C.pdf
- Ghidra dsPIC33F processor definition: https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/Processors/PIC/data/languages/dsPIC33F.slaspec
- Ghidra PIC24/dsPIC shared instruction definition: https://github.com/NationalSecurityAgency/ghidra/blob/master/Ghidra/Processors/PIC/data/languages/PIC24.sinc
