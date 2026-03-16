# PX4 Port — Orqa H7 QuadCore + Wingcore

PX4 flight controller firmware port for the **Orqa H7 QuadCore** and **Orqa H7 Wingcore** (STM32H743VIH6, 8 MHz HSE).

> **Status: Phase 2 Complete — Full board definition with all sensors, motors, servos, and peripherals configured. Ready for hardware validation.**

---

## Hardware

The QuadCore and Wingcore are **the same PCB**. PX4 handles quad vs fixed-wing at the airframe level.

| Component | Details |
|-----------|---------|
| MCU | STM32H743VIH6 (LQFP-100) |
| HSE Crystal | 8 MHz → 480 MHz SYSCLK |
| IMU 1 | ICM-42688-P on SPI1 — CS=PA4, DRDY=PC3, rotation CW270 |
| IMU 2 | ICM-42688-P on SPI4 — CS=PE11, DRDY=PE10, rotation CW180 |
| Barometer | DPS310 on I2C2 @ 0x77 |
| Magnetometer | QMC5883 on I2C1 (external) |
| OSD | MAX7456 on SPI3 — CS=PA15 |
| Flash | W25Q128FV on SPI2 — CS=PB12 |
| CAN | FDCAN1 — RX=PB8, TX=PB9 |
| Motors | 8 outputs: TIM4(PD12/PD13), TIM2(PA1/PA0), TIM5(PA2/PA3), TIM3(PB1/PB0) |
| Servos | 2 outputs: TIM15(PE6/PE5) |
| Board ID | QuadCore=1099, Wingcore=1100 (development IDs) |

### Pin Map Sources

Pin assignments were cross-validated from three independent sources:
- **Betaflight 4.4.1** ORQAH7QuadCore unified target config
- **ArduPilot** OrqaH7QuadCore hwdef.dat (mainline)
- **Hardware schematic** (STM32H743VIH6 — IC8A/IC8B/IC8C)

---

## What Works

- [x] Firmware compiles against PX4
- [x] Bootloader compiles
- [x] Board target discoverable by PX4 build system
- [x] Docker build wrapper (`build.sh`)
- [x] Full GPIO pin map — all sensors, buses, and outputs configured
- [x] Dual ICM42688P with correct rotations
- [x] DPS310 barometer on I2C2
- [x] QMC5883 magnetometer on I2C1
- [x] MAX7456 OSD on SPI3
- [x] W25Q128FV dataflash on SPI2
- [x] 8 motor + 2 servo timer/DMA mapping
- [x] CAN bus enabled (FDCAN1)
- [x] SDMMC1 microSD support
- [x] 3 status LEDs (PA8/PA10/PD11)
- [x] Buzzer on PE9 (TIM1_CH1)
- [x] Battery voltage (PC0) and current (PC1) ADC
- [x] Camera switch GPIO (PD0)
- [x] Wingcore fixed-wing variant

## What Needs Hardware Validation

- [ ] Flash and boot on actual ORQA H7 hardware
- [ ] Verify IMU rotation values match physical orientation
- [ ] Confirm UART ttyS mapping under NuttX serial reordering
- [ ] DShot ESC communication on motor outputs
- [ ] QGroundControl connection and parameter storage
- [ ] Flight test (quad and fixed-wing)

---

## Build Targets

| Target | Command | Use Case |
|--------|---------|----------|
| QuadCore firmware | `make orqa_h7quadcore_default` | Multirotor |
| QuadCore bootloader | `make orqa_h7quadcore_bootloader` | Bootloader |
| Wingcore firmware | `make orqa_h7wingcore_default` | Fixed-wing |
| Wingcore bootloader | `make orqa_h7wingcore_bootloader` | Bootloader |

---

## Prerequisites

- [Docker Desktop](https://docs.docker.com/desktop/install/windows-install/) (Windows) or Docker (Linux/macOS)
- Git
- WSL2 (Windows only — required for Docker build)
- 8 GB RAM recommended

---

## Build Instructions

### 1. Clone PX4-Autopilot

Clone into a directory called `PX4-Autopilot` **alongside** this repo:

```bash
git clone --recursive https://github.com/PX4/PX4-Autopilot.git
```

Your directory structure should look like:
```
parent/
  orqa-h7quadcore-px4/    ← this repo
  PX4-Autopilot/          ← PX4 source
```

### 2. Copy board files into PX4

```bash
cp -r boards/orqa PX4-Autopilot/boards/
```

### 3. Build firmware (Linux/macOS)

```bash
cd PX4-Autopilot
make orqa_h7quadcore_default    # quad
make orqa_h7wingcore_default    # fixed-wing
```

### 4. Build firmware (Windows via WSL2 + Docker)

```bash
./build.sh
```

---

## Output Artifacts

| File | Description |
|------|-------------|
| `build/orqa_h7quadcore_default/orqa_h7quadcore_default.px4` | QuadCore firmware (flash via QGroundControl) |
| `build/orqa_h7quadcore_default/orqa_h7quadcore_default.bin` | QuadCore raw binary |
| `build/orqa_h7quadcore_bootloader/orqa_h7quadcore_bootloader.bin` | QuadCore bootloader (flash via DFU) |
| `build/orqa_h7wingcore_default/orqa_h7wingcore_default.px4` | Wingcore firmware |
| `build/orqa_h7wingcore_default/orqa_h7wingcore_default.bin` | Wingcore raw binary |

---

## Flashing

### Step 1 — Flash bootloader via DFU

1. Hold BOOT button and connect USB-C (or short BOOT0 to 3V3)
2. Verify DFU mode: `dfu-util -l` should show STM32 device
3. Flash:
   ```bash
   dfu-util -a 0 --dfuse-address 0x08000000 -D \
     PX4-Autopilot/build/orqa_h7quadcore_bootloader/orqa_h7quadcore_bootloader.bin
   ```

### Step 2 — Flash firmware via QGroundControl

1. Unplug and replug USB (no BOOT button needed)
2. Open QGroundControl → Vehicle Setup → Firmware
3. Select PX4 Pro → Advanced → Custom firmware
4. Choose the `.px4` file for your target

---

## Peripheral Map

### SPI Buses

| Bus | SCK | MISO | MOSI | Device | CS | DRDY |
|-----|-----|------|------|--------|----|------|
| SPI1 | PA5 | PA6 | PA7 | ICM42688P #1 | PA4 | PC3 |
| SPI2 | PB13 | PB14 | PB15 | W25Q128FV Flash | PB12 | — |
| SPI3 | PB3 | PB4 | PD6 | MAX7456 OSD | PA15 | — |
| SPI4 | PE12 | PE13 | PE14 | ICM42688P #2 | PE11 | PE10 |

### I2C Buses

| Bus | SCL | SDA | Devices |
|-----|-----|-----|---------|
| I2C1 | PB6 | PB7 | Magnetometer (QMC5883), external |
| I2C2 | PB10 | PB11 | DPS310 Barometer @ 0x77 |

### UARTs

| UART | TX | RX | Default Function |
|------|----|----|-----------------|
| USART3 | PD8 | PD9 | RC Input (GHST) |
| USART6 | PC6 | PC7 | MAVLink Telemetry |
| UART7 | PE8 | PE7 | GPS |
| UART8 | — | PE0 | ESC Telemetry (RX only) |

### Motor / Servo Outputs

| Output | Pin | Timer | Channel | Function |
|--------|-----|-------|---------|----------|
| PWM1 | PD12 | TIM4 | CH1 | Motor 1 |
| PWM2 | PD13 | TIM4 | CH2 | Motor 2 |
| PWM3 | PA1 | TIM2 | CH2 | Motor 3 |
| PWM4 | PA0 | TIM2 | CH1 | Motor 4 |
| PWM5 | PA2 | TIM5 | CH3 | Motor 5 |
| PWM6 | PA3 | TIM5 | CH4 | Motor 6 |
| PWM7 | PB1 | TIM3 | CH4 | Motor 7 |
| PWM8 | PB0 | TIM3 | CH3 | Motor 8 |
| PWM9 | PE6 | TIM15 | CH2 | Servo 1 (Aileron on Wingcore) |
| PWM10 | PE5 | TIM15 | CH1 | Servo 2 (Elevator on Wingcore) |

### IMU Rotations (Verified)

Rotations were derived from the PCB layout, ICM-42688-P datasheet axis diagram, and cross-validated against Betaflight and ArduPilot configs. See [`boards/orqa/h7quadcore/docs/`](boards/orqa/h7quadcore/docs/) for PCB layout images.

| IMU | Mount | BF Rotation | ArduPilot Rotation | PX4 Rotation |
|-----|-------|-------------|-------------------|--------------|
| Gyro 1 (SPI1) | Bottom-mounted | CW270 | ROLL_180_YAW_270 | ROTATION_ROLL_180_YAW_270 (R6) |
| Gyro 2 (SPI4) | Bottom-mounted | CW180 | PITCH_180 | ROTATION_PITCH_180 (R12) |

**Gyro 1 derivation:** PCB layout shows Pin 6 (INT1/GYRO_1_EXTI) at the top-left of the footprint. In the datasheet, Pin 6 is left-side mid-bottom, confirming the chip is physically rotated. ArduPilot's `ROLL_180` component indicates Z-axis inversion (bottom-mount), `YAW_270` gives the in-plane rotation.

**Gyro 2 derivation:** PCB layout shows Pin 1 (MISO) at top-left and Pin 4 (GYRO_2_EXTI) at bottom-left. ArduPilot's `PITCH_180` indicates 180° flip about the Y-axis (bottom-mount with different orientation than Gyro 1).

> **Note:** The Gyro 2 PCB footprint labels its nets as "SPI3_*" but the schematic and all firmware configs (BF, ArduPilot) map it to SPI4 (PE11-PE14). This is a PCB tool labeling artifact — the schematic is authoritative.

### Other

| Function | Pin |
|----------|-----|
| LED 0 (Red) | PA8 |
| LED 1 (Green) | PA10 |
| LED 2 (Blue) | PD11 |
| Buzzer | PE9 (TIM1_CH1) |
| USB VBUS | PA9 |
| Camera Switch | PD0 |
| VBAT ADC | PC0 (ADC1_CH10) |
| Current ADC | PC1 (ADC1_CH11) |
| CAN RX | PB8 |
| CAN TX | PB9 |
| SDMMC1 | PC8/PC9/PC10/PC11/PC12/PD2 |

---

## Project Structure

```
boards/
  orqa/
    h7quadcore/              QuadCore board support (multirotor defaults)
      default.px4board       Module/driver selection
      bootloader.px4board    Bootloader build config
      firmware.prototype     Board ID, flash size
      init/                  Startup scripts (sensors, defaults, extras)
      nuttx-config/          NuttX OS config (clocks, peripherals, linker)
      src/                   Board C/C++ source (pins, SPI, I2C, timers, LEDs)
    h7wingcore/              Wingcore board support (fixed-wing defaults)
      ...                    Same structure, different autostart + servo defaults
build.sh                     Docker build wrapper for Windows
ORQA_PIN_REQUEST.md          Historical — pin request (now resolved)
.planning/                   Project planning documents
```

---

## Roadmap

| Phase | Goal | Status |
|-------|------|--------|
| 1 — Scaffold and Build | Clean-compiling BSP + Docker build wrapper | ✅ Complete |
| 2 — Pin Map and Sensors | Full GPIO map, all sensor/peripheral configs | ✅ Complete |
| 3 — Hardware Validation | Flash to hardware, verify boot and sensors | ⏳ Next |
| 4 — Motor Outputs | DShot ESC bring-up, motor test | 📋 Planned |
| 5 — Flight Validation | Full flight test, parameter tuning | 📋 Planned |
| 6 — Upstream PR | Register board IDs, submit to PX4 mainline | 📋 Planned |

---

## Board Template

Based on the **Holybro KakuteH7** PX4 board definition (same STM32H743, same 8 MHz HSE, same 480 MHz clock tree). The KakuteH7 dual-IMU variant was used as the reference for dual ICM42688P configuration.

---

## Contributing

If you have an Orqa H7 QuadCore or Wingcore board and can test:

1. **DFU flash** — does the bootloader flash and does the board enumerate over USB?
2. **QGroundControl connection** — does QGC see the board after firmware flash?
3. **Sensor check** — run `listener sensor_accel` and `listener sensor_baro` on the nsh console
4. **Motor test** — use QGC motor test page with props off

Please open an issue or contact [@DroneWuKong](https://github.com/DroneWuKong) with results.
