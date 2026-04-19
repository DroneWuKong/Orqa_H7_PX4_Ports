# ORQA PX4 Port — Session Context
## For: DroneWuKong/orqa-h7quadcore-px4
## Last updated: 2026-03-16

---

## What This Project Is

PX4 flight controller firmware port for ORQA H7 QuadCore and Wingcore flight controllers (STM32H743VIH6). Both boards are the same PCB — QuadCore is multirotor, Wingcore is fixed-wing. A single hardware definition covers both; they differ only in default airframe parameters and servo assignments.

## Repo: https://github.com/DroneWuKong/orqa-h7quadcore-px4

---

## Current State: Phase 2 Complete

### What's Done
- Complete PX4 board definitions for both QuadCore (`boards/orqa/h7quadcore/`) and Wingcore (`boards/orqa/h7wingcore/`)
- Full GPIO pin map cross-validated from 4 sources: Betaflight 4.4.1 unified config, ArduPilot mainline hwdef.dat, hardware schematic, and ORQA's official PX4 fork
- Aligned with ORQA official PX4 fork (`orqafpv/PX4-Autopilot` branch `develop_h743-3030-pro`)
- IMU rotations physically verified from PCB layout: SPI1=R12 (ROTATION_PITCH_180), SPI4=R14 (ROTATION_ROLL_180_YAW_90)
- ArduPilot OrqaF405Pro hwdef bugfix prepared (patch in `ardupilot-fixes/`)

### What's Blocked (needs hardware)
- Flash and boot on actual ORQA H7 hardware
- UART ttyS mapping verification
- DShot ESC communication
- QGroundControl connection
- Flight test

---

## Key Technical Details

### MCU & Clock
- STM32H743VIH6, LQFP-100, 8 MHz HSE → 480 MHz SYSCLK
- Clock tree identical to KakuteH7 (board.h copied from that target)
- Board ID: 1013 (matches ORQA official)

### IMUs (Dual)
- **SPI1**: MPU6000 (v1.1 boards) or ICM42688P (later revs), CS=PA4, rotation R12 (ROTATION_PITCH_180)
  - Physical: 180° CW yaw to face forward, bottom-mounted
- **SPI4**: ICM42688P, CS=PE11, DRDY=PE10, rotation R14 (ROTATION_ROLL_180_YAW_90)
  - Physical: 90° CCW yaw to face forward, bottom-mounted
- rc.board_sensors tries MPU6000 first on SPI1, falls back to ICM42688P

### Peripherals
- Baro: DPS310 on I2C2 @ 0x77
- Mag: QMC5883 on I2C1 @ 0x0D (external)
- OSD: MAX7456 on SPI3, CS=PA15
- Flash: W25Q128FV on SPI2, CS=PB12
- CAN: FDCAN1, RX=PB8, TX=PB9
- SD: SDMMC1 (PC8/PC9/PC10/PC11/PC12/PD2)

### PWM Outputs (11 total)
Motor ordering matches ORQA official (NOT Betaflight order):
1. PB0  TIM3_CH3 (MOTOR_8, MFC J6)
2. PB1  TIM3_CH4 (MOTOR_7, MFC J6)
3. PA1  TIM5_CH2 (MOTOR_3, ESC J2)
4. PA0  TIM5_CH1 (MOTOR_4, ESC J2)
5. PA2  TIM5_CH3 (MOTOR_5, MFC J6)
6. PA3  TIM5_CH4 (MOTOR_6, MFC J6)
7. PD13 TIM4_CH2 (MOTOR_1, ESC J2)
8. PD12 TIM4_CH1 (MOTOR_2, ESC J2)
9. PD14 TIM4_CH3 (SERVO_3)
10. PE5  TIM15_CH1 (SERVO_2)
11. PE6  TIM15_CH2 (SERVO_1)

**WARNING**: Enabling CAN bus disables all Timer5 outputs (motors 3-6) — known PX4 bug as of Feb 2025.

### UARTs
- USART3 (PD8/PD9): RC input, GHST, singlewire — ttyS0
- USART6 (PC6/PC7): Serial console / MAVLink telemetry — ttyS1
- UART7 (PE8/PE7): GPS — ttyS2
- UART8 (PE0 RX only): DShot ESC telemetry — ttyS3

### Other
- LEDs: PA8 (blue), PA10 (green) — PUSHPULL, active low
- Buzzer: PE9 TIM1_CH1
- USB VBUS: PE2
- Camera switch: PD0
- HRT timer: TIM2
- Battery: V_DIV=9.2931, A_PER_V=92.6, 6S default

---

## Known Differences from ORQA Official Fork

Our port adds beyond the official:
- Wingcore fixed-wing variant (SYS_AUTOSTART=2100, servo assignments)
- ICM42688P fallback on SPI1 for newer board revisions
- Extra defaults (CBRK_SUPPLY_CHK, SYS_HAS_MAG, EKF2_IMU_CTRL, DSHOT_CONFIG)
- Third LED on PD11 mapped (LED_2/blue in our config)
- PCB layout documentation images for IMU rotation verification

Our port omits vs official:
- `dataman start -f /fs/mtd_waypoints` (SPI flash waypoint storage)
- Sik radio setup comments in defaults
- Some board_config.h defines (RC_SERIAL_PORT, BOARD_HAS_PWM, DIRECT_INPUT_TIMER_CHANNELS)

These are non-breaking differences. The critical paths (SPI, timers, DMA, rotations, board ID) are identical.

---

## ArduPilot F405Pro Fix

Patch in `ardupilot-fixes/OrqaF405Pro/`:
- Removed duplicate SPIDEV imu2 (same bus/CS as imu1)
- Fixed README battery pins (VOLT_PIN 13→11, CURR_PIN 12→13)
- PR description template included
- Needs: Fork ArduPilot/ardupilot to DroneWuKong, push branch, open PR

---

## Reference Sources Used

| Source | Location | What it provided |
|--------|----------|-----------------|
| BF 4.4.1 config | Uploaded ORQAH7QuadCore.config | Pin map, timer/DMA, serial functions |
| ArduPilot hwdef | `ardupilot/libraries/AP_HAL_ChibiOS/hwdef/OrqaH7QuadCore/hwdef.dat` | Pin map, IMU rotations, CAN pins, SDMMC |
| ORQA PX4 fork | `github.com/orqafpv/PX4-Autopilot` branch `develop_h743-3030-pro` | Official sensor init, motor order, board ID, battery params |
| Hardware schematic | Project file image_3.png | STM32H743VIH6 pinout (IC8A/IC8B/IC8C) |
| PCB layout photos | Uploaded gyro footprint images | IMU physical orientation verification |
| iNav 7.1.2 hex | Uploaded ORQAH743 binary | Sensor identification via string extraction |
| iNav 8.0.0 hex | Uploaded ORQAH743WING binary | Confirmed QuadCore = Wingcore (same hardware) |
| ArduPlane hex | Uploaded arduplane_with_bl_v1_1.hex | Confirmed "OrqaH743Wing" board name, same hardware |

---

## Next Steps (Phase 3+)

1. **Flash to hardware** — DFU bootloader, then firmware via QGC
2. **Verify ttyS mapping** — `nsh> ls /dev/ttyS*` and test each UART
3. **Sensor validation** — `listener sensor_accel`, `listener sensor_baro`
4. **DShot test** — motor test in QGC with props off
5. **Flight test** — quad first, then fixed-wing with wingcore
6. **Upstream PR** — submit to PX4 mainline after flight validation

---

## Build Commands

```bash
# Copy boards into PX4
cp -r boards/orqa /path/to/PX4-Autopilot/boards/

# Build
cd PX4-Autopilot
make orqa_h7quadcore_default    # quad
make orqa_h7wingcore_default    # fixed-wing
make orqa_h7quadcore_bootloader # bootloader
```

---

## Update: April 19 2026 — CAN Node OSD Architecture

OSD-1 resolved: no spare SPI bus on H743 (SPI1=IMU, SPI2=Flash, SPI3=OSD, SPI4=IMU).

**Chosen architecture: STM32G0B1 CAN node**
- Taps FDCAN1 bus (PB8/PB9) in BUS_MONITORING (silent) mode
- Listens for DroneCAN Fix2 + NodeStatus — never transmits, zero bus impact
- Timer5/CAN PX4 bug is irrelevant — PX4 keeps FDCAN1 disabled, node hangs
  off the physical bus passively
- Node is SPI master to H503 via a NEW second CS line (CS2, free H503 GPIO)
- H743 keeps CS1=PA15 for standard MAX7456 OSD — no sharing, no mutex
- Full spec: DroneWuKong/1G-FDMA osd/can-node-spec.md

**SPI3 pin confirmation (cross-validated):**
- board.h comment "SPI2 is OSD" is a copy-paste error from reference board
- spi.cpp is correct: SPI3, CS=PA15
- PROJECT_CONTEXT confirms: SCK=PB03, MISO=PB04, MOSI=PD06, CS=PA15

**Open questions for hardware phase (add to Phase 3 checklist):**
- CAN-3: Free GPIO on H503 for CS2?
- CAN-5: DroneCAN baud rate — 1 Mbps or 500 kbps?
