# Orqa PX4 Board Ports

PX4 v1.15.4 board ports for the **Orqa H7 QuadCore**, **H7 Wingcore**,
the FC side of the **DTK APB**, and the **F405 Pro**.

This repository contains the board definitions plus a small, reviewed
[PX4 storage patch](patches/0001-orqa-storage.patch). Use the installer below;
copying only `boards/orqa` is no longer sufficient.

> **Status:** all seven application/bootloader targets are continuously built;
> physical-board validation is still required before flight use.

[![Build PX4 ports](https://github.com/DroneWuKong/Orqa_H7_PX4_Ports/actions/workflows/build.yml/badge.svg)](https://github.com/DroneWuKong/Orqa_H7_PX4_Ports/actions/workflows/build.yml)

## Precompiled firmware

The first hardened build is published as a **hardware-unvalidated prerelease**.
Use the application `.px4` files with QGroundControl's **Custom firmware**
option. Flash bootloader `.bin` files only through STM32 DFU and only if you
intend to replace the installed bootloader.

| Board | Application | Bootloader |
|-------|-------------|------------|
| H7 QuadCore | [Download `.px4`](https://github.com/DroneWuKong/Orqa_H7_PX4_Ports/releases/download/v0.1.0-rc1/orqa_h7quadcore_default.px4) | [Download `.bin`](https://github.com/DroneWuKong/Orqa_H7_PX4_Ports/releases/download/v0.1.0-rc1/orqa_h7quadcore_bootloader.bin) |
| H7 Wingcore | [Download `.px4`](https://github.com/DroneWuKong/Orqa_H7_PX4_Ports/releases/download/v0.1.0-rc1/orqa_h7wingcore_default.px4) | [Download `.bin`](https://github.com/DroneWuKong/Orqa_H7_PX4_Ports/releases/download/v0.1.0-rc1/orqa_h7wingcore_bootloader.bin) |
| DTK APB | [Download `.px4`](https://github.com/DroneWuKong/Orqa_H7_PX4_Ports/releases/download/v0.1.0-rc1/orqa_apb_default.px4) | [Download `.bin`](https://github.com/DroneWuKong/Orqa_H7_PX4_Ports/releases/download/v0.1.0-rc1/orqa_apb_bootloader.bin) |
| F405 Pro | [Download `.px4`](https://github.com/DroneWuKong/Orqa_H7_PX4_Ports/releases/download/v0.1.0-rc1/orqa_f405pro_default.px4) | Use the factory ArduPilot bootloader |

[View all release assets and checksums](https://github.com/DroneWuKong/Orqa_H7_PX4_Ports/releases/tag/v0.1.0-rc1).

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
| Motors | 8 outputs: TIM4(PD12/PD13), TIM2(PA0-PA3), TIM3(PB0/PB1) |
| Servos | 3 outputs: TIM4(PD14), TIM15(PE5/PE6) |
| Board ID | 1204 (`AP_HW_ORQAH7QUADCORE`, registered in mainline `board_types.txt`) |
| USB (PX4 firmware) | `0x35b6:0x0091` (Orqa VID; matches factory ArduPlane image) |

### Pin Map Sources

Pin assignments were cross-validated from four independent sources:
- **ORQA official PX4 fork** — [`orqafpv/PX4-Autopilot` develop_h743-3030-pro branch](https://github.com/orqafpv/PX4-Autopilot/tree/develop_h743-3030-pro)
- **Betaflight 4.4.1** ORQAH7QuadCore unified target config
- **ArduPilot** OrqaH7QuadCore hwdef.dat (mainline)
- **Hardware schematic** (STM32H743VIH6 — IC8A/IC8B/IC8C)

---

## What Works

The CI matrix builds each target from a clean, recursive PX4 v1.15.4 checkout.
See [Build Verification](#build-verification) for the exact target list.

- [x] Four application firmwares compile and link against PX4 v1.15.4
- [x] Three H7 bootloaders compile and link
- [x] Board targets discoverable by the PX4 build system
- [x] Docker build wrapper (`build.sh`)
- [x] Full GPIO pin map — all sensors, buses, and outputs configured
- [x] Dual IMU (SPI1 MPU6000/ICM42688P, SPI4 ICM42688P; APB SPI4 ICM42605/ICM42688P) with per-chip rotations, both devtypes registered per bus
- [x] DPS310 barometer on I2C2
- [x] QMC5883 magnetometer on I2C1
- [x] MAX7456 OSD on SPI3
- [x] W25Q128FV dataflash on SPI2
- [x] 8 motor + 3 servo timer/DMA mapping on H7; 8 motors on F405 Pro
- [x] CAN bus (FDCAN1) pins defined for the PX4 UAVCAN driver
- [x] 3 status LEDs (PA8/PA10/PD11)
- [x] Buzzer on PE9 (TIM1_CH1)
- [x] Battery voltage (PC0) and current (PC1) ADC
- [x] Camera switch GPIO (PD0)
- [x] QuadCore/Wingcore SDMMC1 driver compiled and initialized
- [x] Wingcore fixed-wing variant; APB companion (i.MX8M Plus) MAVLink on UART4 @ 230400
- [x] F405 Pro OSD, corrected LED/ADC mapping, 48 KB factory-bootloader layout,
  and W25Q128-backed parameter/waypoint storage

### Storage status and known gaps

- **QuadCore/Wingcore:** SDMMC1, the NuttX MMC/SD layer, and board startup are
  wired together in firmware. Card detect is not exposed, so firmware assumes
  a card is inserted. Mounting and sustained logging still need hardware tests.
  Failed mounts no longer automatically format the card. Insert the card before
  powering on; removal/reinsertion while running is not supported.
- **DTK APB:** SD remains deliberately disabled. The only published provisional
  SDMMC2 map overlaps active flash, OSD, and ADC pins; enabling it without a
  confirmed APB schematic would corrupt other peripherals.
- **F405 Pro:** the board has no microSD socket. SPI2 is the OSD bus, not an SD
  bus. Parameters and waypoints use the onboard SPI3 W25Q128 dataflash.

### Storage hardening after rc1

The rc1 F405 image compiled, but its SPI manifest selected PX4's FRAM driver;
that did **not** establish working W25 storage. The storage patch adds explicit
SPI NOR attachment through NuttX's W25 driver and fixes a zero-partition
division during MTD initialization. All four application targets now use one
shared, erase-aligned W25 partition definition and a conservative 10 MHz clock:

| Board | Parameters | Missions, fences and rally points | Flight logs |
|-------|------------|----------------------------------|-------------|
| QuadCore / Wingcore | Existing internal flash sector | 256 KiB W25 partition on SPI2 | microSD |
| APB | Existing internal flash sector | 256 KiB W25 partition on SPI2 | MAVLink streaming; SD disabled |
| F405 Pro | 64 KiB W25 partition on SPI3 | Separate 256 KiB W25 partition on SPI3 | MAVLink streaming; no SD socket |

`SYS_DM_BACKEND=0` selects the W25 mission partition when initialized, falling
back to PX4's normal SD path if unavailable. Explicit RAM (`1`) and disabled
(`-1`) selections are respected. W25 is not a filesystem for ULog files.
These changes are source- and build-tested; physical persistence is still
unverified. Save parameters and missions through QGroundControl before
upgrading, and re-upload missions after changing storage backends. The new
partitions may overwrite external-flash data from other firmware.

H7 calibration remains in its existing internal-flash sector. Old SD parameter
files are no longer imported automatically or used to trigger a reboot. If
needed, import a reviewed backup explicitly with `param import <path>` followed
by `param save`.

H7 builds omit embedded command help text to recover flash space while keeping
the flight modules, parameter metadata and diagnostic commands. Consult the
[PX4 module reference](https://docs.px4.io/v1.15/en/modules/) for command usage.
QuadCore/Wingcore now include `sd_bench` and `sd_stress`; see
[bench validation](docs/bench-validation.md) for the storage test procedure.

Output protocols use PX4 v1.15's `PWM_MAIN_TIMn` parameters; the obsolete
`DSHOT_CONFIG` setting has been removed. QuadCore, APB and F405 default their
motor timer groups to DShot300. On H7, PWM9 shares TIM4 with PWM7/8 and cannot
drive a conventional servo while that group is DShot; PWM10/11 have a separate
50 Hz servo timer. Wingcore defaults all groups to 50 Hz PWM and leaves actuator
functions for aircraft-specific setup in QGroundControl. Verify every output
and its direction with propellers removed, especially after upgrading existing
settings: board defaults do not overwrite explicitly saved parameter values.

## Build Verification

Release `v0.1.0-rc1` was built in GitHub Actions with PX4's pinned
`px4io/px4-dev-nuttx-focal` image and GCC 9.3.1 against a clean recursive PX4
**v1.15.4** checkout:

| Target | FLASH usage | Result |
|--------|-------------|--------|
| `orqa_h7quadcore_default` | 1,531,688 / 1,572,864 bytes (97.38%) | Pass |
| `orqa_h7quadcore_bootloader` | 384 KB reserved region | Pass |
| `orqa_h7wingcore_default` | 1,548,628 / 1,572,864 bytes (98.46%) | Pass |
| `orqa_h7wingcore_bootloader` | 384 KB reserved region | Pass |
| `orqa_apb_default` | 1,525,324 / 1,572,864 bytes (96.98%) | Pass |
| `orqa_apb_bootloader` | 384 KB reserved region | Pass |
| `orqa_f405pro_default` | 951,729 / 999,424 bytes (95.23%) | Pass |

The 1536 KB app partition (a consequence of the 384 KB ArduPilot-compatible
bootloader reservation) does not fit PX4's full "everything" module set, so
each target carries an **airframe-appropriate** selection: quadcore + APB are
multirotor (`SYS_AUTOSTART 4001`), wingcore is fixed-wing (`SYS_AUTOSTART
2100`, with the core MC controllers kept because PX4 v1.15 libraries reference
their parameters). Optional payload/legacy modules (SIH sim, gyro-FFT, DDS,
landing-target, and camera/gimbal/smart-battery drivers) are trimmed to fit.
The build matrix is the source of truth for continued flash-fit checks.
Every new build verifies board ID, bundle/raw-image equality, reset vector,
ELF load address, partition size and at least 16 KiB of free application flash.
Per-target `.manifest.json` files record source revisions, input hashes,
artifact checksums and the measured budget.

## What Needs Hardware Validation

- [ ] Flash and boot on actual ORQA H7 hardware
- [ ] Verify source-derived IMU rotations on each physical board revision
- [ ] Verify the derived UART ttyS mapping on hardware (APB companion baud is
  field-confirmed at 230400)
- [ ] DShot ESC communication on motor outputs
- [ ] QGroundControl connection and parameter storage
- [ ] QuadCore/Wingcore SD mount, hot-start behavior, and sustained ULog write
- [ ] F405 W25Q128 parameter persistence and MAX7456 video output
- [ ] Flight test (quad and fixed-wing)

---

## Build Targets

| Target | Command | Use Case |
|--------|---------|----------|
| QuadCore firmware | `make orqa_h7quadcore_default` | Multirotor |
| QuadCore bootloader | `make orqa_h7quadcore_bootloader` | Bootloader |
| Wingcore firmware | `make orqa_h7wingcore_default` | Fixed-wing |
| Wingcore bootloader | `make orqa_h7wingcore_bootloader` | Bootloader |
| DTK APB FC firmware | `make orqa_apb_default` | APB integrated FC (app @ 0x08060000) |
| DTK APB PX4 bootloader | `make orqa_apb_bootloader` | Optional factory-bootloader replacement |
| F405 Pro firmware | `make orqa_f405pro_default` | F405 multirotor (factory bootloader) |

---

## Prerequisites

- [Docker Desktop](https://docs.docker.com/desktop/install/windows-install/) (Windows) or Docker (Linux/macOS)
- Git and Python 3.8 or newer
- WSL2 (Windows only — required for Docker build)
- 8 GB RAM recommended

---

## Build Instructions

### 1. Clone PX4-Autopilot

Clone into a directory called `PX4-Autopilot` **alongside** this repo:

```bash
git clone --branch v1.15.4 --recursive https://github.com/PX4/PX4-Autopilot.git
```

Your directory structure should look like:
```
parent/
  Orqa_H7_PX4_Ports/      ← this repo
  PX4-Autopilot/          ← PX4 source
```

### 2. Build with the wrapper

```bash
./build.sh orqa_h7quadcore_default
```

The wrapper verifies the exact PX4 v1.15.4 commit, installs the board definitions
and storage patch, then uses the pinned PX4 NuttX Docker image. Pass any target
from the table above. The installer can be rerun and refuses to overwrite local
edits. Use a fresh PX4 checkout when upgrading an older manually copied overlay.

### 3. Build directly (Linux/macOS)

```bash
python3 scripts/install.py ../PX4-Autopilot
cd ../PX4-Autopilot
make orqa_h7quadcore_default    # quad
make orqa_h7wingcore_default    # fixed-wing
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
| `build/orqa_h7wingcore_bootloader/orqa_h7wingcore_bootloader.bin` | Wingcore bootloader |
| `build/orqa_apb_default/orqa_apb_default.px4` | DTK APB FC firmware |
| `build/orqa_apb_bootloader/orqa_apb_bootloader.bin` | DTK APB bootloader |
| `build/orqa_f405pro_default/orqa_f405pro_default.px4` | F405 Pro firmware |

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

## Orqa DTK APB variant

The **Orqa DTK APB** is a single-board flight computer: this same STM32H743 FC
circuit plus an NXP i.MX8M Plus companion SOC (4×A53 + M7, 2.25 TOPS NPU,
H.265 encode, dual MIPI-CSI). The `boards/orqa/apb` target covers the FC side.
See [`reference/orqa-apb/README.md`](reference/orqa-apb/README.md) for the
factory hwdef-bl and firmware-image analysis behind these values.

Differences from the quadcore/wingcore targets:

| Item | QuadCore / Wingcore | DTK APB |
|------|--------------------|---------|
| Board ID | 1204 (registered, matches mainline AP bootloader) | 1189 (confirmed from the MRM2-10 AI factory image) |
| USB PID | `0x35b6:0x0091` | `0x35b6:0x0090` (matches ORQA's official PX4 APB target) |
| IMU probing | SPI1: MPU6000 → ICM42688P (R12); SPI4: ICM42688P (R14) | SPI1: MPU6000 → ICM42688P (R12); SPI4: ICM42605 (R12) → ICM42688P (R14) |
| SD card | SDMMC1 (PC8-PC12/PD2), firmware enabled | Disabled: provisional SDMMC2 pins conflict with active peripherals |
| Companion link | — | **UART4 (PC10/PC11) = TEL1 @ 230400** to the i.MX8M Plus; `MAV_0` defaults to ONBOARD |
| Serial map (ttyS0…) | USART3 RC, USART6 TEL1, UART7 GPS, UART8 ESC | USART3 RC, UART4 TEL1 (IMX), USART6 TEL2 (SiK/gimbal), UART7 GPS, UART8 ESC (TEL3) |

APB serial/sensor configuration is aligned with **ORQA's official PX4 APB
target** ([`orqafpv/PX4-Autopilot` branch `develop_APB-initial`](https://github.com/orqafpv/PX4-Autopilot/tree/develop_APB-initial),
`boards/orqa/h743-APB`), which also confirmed the UART4 "IMX" bridge pins
and the ICM42605-on-SPI4 rotation. That branch keeps the classic PX4 flash
layout (`0x08020000`, board ID 1013 — the Matek collision this port fixes);
we intentionally diverge to the AP-compatible layout + registered IDs below.

**All three targets share the ArduPilot-compatible flash layout:** bootloader
in sectors 0-2 (384 KB, matching `FLASH_BOOTLOADER_LOAD_KB 384` in every Orqa
ArduPilot hwdef-bl), app at `0x08060000` (1536 KB max), params in sector 15
(`0x081E0000`).

**Flashing:** ArduPilot bootloaders speak the same serial flashing protocol
as the PX4 bootloader, so QGC / `px_uploader.py` can load a `.px4` through
the ArduPilot bootloader already on the board — no bootloader replacement —
provided the board ID matches:

- **Mainline AP bootloader** (OrqaH7QuadCore, ID 1204): flashes the
  quadcore/wingcore targets directly.
- **Old factory bootloaders** (Orqa-private IDs — 1185 on the v1.1 Wing
  image, 1188 on the orqafpv `h7quadcore` branch): refuse with a board-id
  mismatch; the ID printed in the error is the installed bootloader's true
  value. Either DFU-install a current bootloader (mainline AP or the PX4
  one from this repo) or rebuild with that ID.
- **APB**: `orqa_apb_default.px4` targets the confirmed factory APB bootloader
  ID 1189.

Recovery is always available via STM32 system DFU (`0x0483:0xdf11`, hold
BOOT), and the factory bootloader also exposes DFU reboot (`ENABLE_DFU_BOOT`).

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
| PWM5 | PA2 | TIM2 | CH3 | Motor 5 |
| PWM6 | PA3 | TIM2 | CH4 | Motor 6 |
| PWM7 | PB1 | TIM3 | CH4 | Motor 7 |
| PWM8 | PB0 | TIM3 | CH3 | Motor 8 |
| PWM9 | PD14 | TIM4 | CH3 | Servo 3; shares protocol with PWM7/8 |
| PWM10 | PE5 | TIM15 | CH1 | Servo 2 |
| PWM11 | PE6 | TIM15 | CH2 | Servo 1 |

### IMU Rotations (Verified)

Rotations verified from PCB layout analysis, physical measurement, and cross-referenced against [ORQA's official PX4 fork](https://github.com/orqafpv/PX4-Autopilot/tree/develop_h743-3030-pro). See [`boards/orqa/h7quadcore/docs/`](boards/orqa/h7quadcore/docs/) for PCB layout images.

| IMU | Bus | Mount | Physical | PX4 Rotation |
|-----|-----|-------|----------|--------------|
| MPU6000 / ICM42688P | SPI1 | Bottom | 180° CW to face forward | ROTATION_PITCH_180 (R12) |
| ICM42688P | SPI4 | Bottom | 90° CCW to face forward | ROTATION_ROLL_180_YAW_90 (R14) |

> **Note:** SPI1 carries an MPU6000 on v1.1 boards and ICM42688P on later revisions. The sensor init script tries MPU6000 first, then falls back to ICM42688P. Both use the same rotation (R12).

> **Note:** The Gyro 2 PCB footprint labels its nets as "SPI3_*" but the schematic and all firmware configs map it to SPI4 (PE11-PE14). This is a PCB tool labeling artifact.

### Other

| Function | Pin |
|----------|-----|
| LED 0 (Red) | PA8 |
| LED 1 (Green) | PA10 |
| LED 2 (Blue) | PD11 |
| Buzzer | PE9 (TIM1_CH1) |
| USB VBUS | PE2 |
| Camera Switch | PD0 |
| VBAT ADC | PC0 (ADC1_CH10) |
| Current ADC | PC1 (ADC1_CH11) |
| CAN RX | PB8 |
| CAN TX | PB9 |
| microSD | Quad/Wing SDMMC1 PC8-PC12/PD2; APB disabled pending a non-conflicting verified map |

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
    apb/                     DTK APB FC support (factory-bootloader layout, ICM42605)
    f405pro/                 F405 Pro support (factory bootloader, external-flash params)
reference/
  orqa-apb/                  Factory hwdef-bl + firmware-image analysis notes
  orqa-f405pro/              F405 hardware and port notes
.github/workflows/build.yml  Clean seven-target CI and release build
build.sh                     Cross-platform Docker build wrapper
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

Based on **ORQA's official PX4 fork** ([`orqafpv/PX4-Autopilot` develop_h743-3030-pro](https://github.com/orqafpv/PX4-Autopilot/tree/develop_h743-3030-pro)) and the **Holybro KakuteH7** PX4 board definition (same STM32H743, same 8 MHz HSE, same 480 MHz clock tree).

Key differences from the ORQA official fork:
- Added Wingcore fixed-wing variant with servo defaults
- SPI1 probes both MPU6000 (v1.1) and ICM42688P (later revisions)
- Added PCB layout documentation for IMU rotation verification
- Moved PA0-PA3 outputs to TIM2 and HRT to TIM8, eliminating the original
  UAVCAN/Timer5 motor-output conflict
- Completed QuadCore/Wingcore SDMMC1 integration

---

## Contributing

If you have an Orqa QuadCore, Wingcore, DTK APB, or F405 Pro board and can test:

1. **DFU flash** — does the bootloader flash and does the board enumerate over USB?
2. **QGroundControl connection** — does QGC see the board after firmware flash?
3. **Sensor check** — run `listener sensor_accel` and `listener sensor_baro` on the nsh console
4. **Motor test** — use QGC motor test page with props off
5. **Storage test** — verify SD logging on Quad/Wing or parameter persistence
   on F405 Pro across a full power cycle

Please open an issue or contact [@DroneWuKong](https://github.com/DroneWuKong) with results.
