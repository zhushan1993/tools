# 硬件配置指南

## M5StickC Plus IoT 引脚定义

```
               ┌──────────────┐
               │   TFT 135x240│
               │  (ST7789v2)  │
┌──────┐      │              │
│ BTN_A│      │              │
│GPIO37│      │              │
│ [确认]│      │  PDM Mic:    │
└──────┘      │  CLK=GPIO0   │
              │  DATA=GPIO34 │
┌──────┐      │  WS=GPIO26   │
│ BTN_B│      │              │
│GPIO39│      │  LED=GPIO10  │
│[录音]│      │              │
└──────┘      └──────────────┘
```

## 刷机步骤

### 首次刷机

```bash
cd firmware
# 编译
platformio run

# 通过 USB 上传
platformio run -t upload

# 查看串口输出（调试用）
platformio device monitor
```

### OTA 更新

如果 M5STICK 已通过 WiFi 连接，可以无线更新：

```bash
# 需要先配置 WiFi
# 编辑 platformio.ini 设置 upload_port 为 M5STICK IP
platformio run -t upload --environment m5stick-c-plus-ota
```

## 蓝牙配对

1. M5STICK 上电后，屏幕显示设备名 `M5Stick-Claude`
2. 电脑打开蓝牙设置，搜索设备
3. 找到 `M5Stick-Claude`，点击配对
4. Linux 下配对后绑定到 rfcomm：

```bash
# 查看 M5STICK 蓝牙地址
bluetoothctl devices | grep M5Stick

# 绑定 rfcomm 设备 (假设 MAC 为 AA:BB:CC:DD:EE:FF)
sudo rfcomm bind /dev/rfcomm0 AA:BB:CC:DD:EE:FF

# 验证
ls -l /dev/rfcomm0
```

## 指示灯说明

| LED 状态 | 含义 |
|----------|------|
| 熄灭 | 待机/休眠 |
| 绿色脉冲 | 蓝牙已连接，待机中 |
| 黄色闪烁 | 等待授权确认 |
| 蓝色闪烁 | 录音中 |
| 白色 | STT 识别中 |
| 红色闪烁 | 错误/断连 |
