# Feature Landscape

**Domain:** PX4 firmware board port (STM32H743, FPV quadcopter)
**Researched:** 2026-03-10
**Confidence note:** Training data through August 2025. Web/Context7 tools unavailable in this session. All claims based on PX4 source analysis knowledge and documented contribution patterns. Confidence noted per section.

---

## Table Stakes

Features without which PX4 will not boot, the quad will not fly, or a PR will not be accepted upstream. Every item here is a blocker.

| Feature | Why Required | Complexity | Notes |
|---------|--------------|------------|-------|
| Board CMake target (`CMakeLists.txt`) | PX4 build system entry point — without this, nothing compiles | Low | Copy from `matek_h743-slim`, rename symbols. One file. |
| NuttX board config (`nuttx-config/`) | OS-level pin/clock/peripheral config. Missing = no boot. | Medium | `defconfig`, `include/board.h`, `src/` init code. H743-specific clock tree (480 MHz, HSE=8MHz). |
| `board_config.h` (hardware description) | Maps logical PX4 names to physical pins. IMU CS, SPI buses, UART assignments, LED pins. | Medium | Must match Orqa hardware exactly. Reference: Betaflight config in PROJECT.md. |
| Linker script (flash/RAM layout) | STM32H743 has split RAM banks — wrong layout = hard faults at boot | Low | Inherit from Matek H743 Slim; only change if memory map differs (unlikely). |
| Bootloader compatibility | PX4 requires PX4 Bootloader on the board; firmware uploads via USB DFU | Low | STM32H743 bootloader is shared across H7 boards; Matek H743 bootloader binary likely works directly. |
| ICM-42688-P driver (SPI) | Primary IMU. PX4 won't arm without at least one healthy gyro/accel. | Low | Driver `icm42688p` exists in PX4 mainline since ~2022. Configuration is in `board_config.h` — declare SPI bus, CS pin, DRDY pin, rotation. |
| Dual ICM-42688 registration | Second IMU (SPI4) must be registered or PX4 logs errors and may complain | Low-Med | Declare both in `board_config.h` with correct rotations (CW270 and CW180). PX4 fuses both via voter. |
| DPS310 barometer driver (I2C) | Required for altitude estimation. Without baro, Altitude/Position modes fail; PX4 may refuse to arm depending on config. | Low | Driver `dps310` exists in PX4 mainline. Declare I2C2 bus, addr 0x77 in board config. |
| DSHOT motor output (8 channels) | FPV ESC3030 requires DSHOT. PWM would work electrically but not for this use case. PX4 DSHOT uses DMA-based TIM channels. | High | Most complex part of the port. Requires correct timer allocation: TIM4 (M1/M2), TIM2 (M3/M4), TIM5 (M5/M6), TIM3 (M7/M8). DMA streams must not conflict. |
| UART assignments (3, 6, 7, 8) | Without UARTs, no RC receiver, no telemetry, no ESC telemetry. PX4 won't function usefully. | Low-Med | Declared in NuttX defconfig and board init. UART3=VTx/receiver, UART6=telemetry, UART7=GPS connector, UART8=ESC telem. |
| USB console / MAVLink over USB | Primary connection for QGroundControl during development and calibration. Without this, no way to interact with the board during bringup. | Low | USB-CDC serial is standard PX4 infrastructure. Board needs USB detect pin (PA9) wired in board_config. |
| Mixer / actuator output config | Tells PX4 which outputs are motors vs servos. Without this, mixer fails and motors don't spin. | Low-Med | `init.d/airframes/` entry or use generic multirotor mixer. For FPV quad, use `4001_quad_x` or similar. |
| ADC (VBAT + current sense) | Battery voltage monitoring. PX4 will warn/refuse operations without valid battery reading. | Low | Declare ADC1 channels: VBAT=PC0, CURR=PC1 in board_config. Scale values from Betaflight config (112/1/12 and 108). |
| LED support (status LEDs) | PX4 uses LEDs to signal arm state, mode, errors. Not strictly boot-blocking but required for usable operation. | Low | 3 LEDs: PA8, PA11, PD11. Map to PX4 LED driver. |
| SD card (microSD) | PX4 logs to SD. Without SD, logging fails silently. SD is near-mandatory for flight validation and debugging. | Low | SDMMC peripheral on H743. Board has microSD slot. NuttX config enables SDMMC. |
| `default.px4board` / `default.cmake` | Build metadata that tells PX4 what modules to include for this target. | Low | Copy from Matek H743 Slim, trim unused modules. |
| Upstream PR: CI must pass | GitHub Actions runs build checks on all board targets. Port must compile cleanly. | Low | Follows automatically if CMake is correct. |
| Upstream PR: `ROMFS/px4fmu_common` or board-specific init | Startup script that runs sensor/driver init at boot. | Low-Med | Customize from H743 Slim template to match Orqa sensor addresses and buses. |

---

## Differentiators

Features that go beyond boot/fly minimum. Valuable for the FPV use case or for a polished upstream contribution, but the quad flies without them.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Bidirectional DSHOT (RPM telemetry) | DSHOT bidir gives per-motor RPM to PX4's dynamic notch filter. Dramatically improves vibration rejection without manual tuning. The Betaflight config already uses bidir — matching this in PX4 is the ideal end state. | High | PX4 DSHOT bidir support added ~2022 for H7. Requires DMA timer config changes. Defer until unidirectional DSHOT is validated. |
| W25Q128 SPI flash (blackbox) | 16MB flash on SPI2 for flight logs without SD card. Useful for race setups without SD. | Medium | Driver `w25q` exists. Declare SPI2 in board config. Requires `ROMFS` mount point for dataman or logger. |
| Beeper / buzzer (TIM1CH1, PE9) | Audible arming/disarming tones. PX4 supports buzzer via `tone_alarm` driver. | Low | Straightforward: declare TIM1CH1 in NuttX config. Optional but improves UX significantly. |
| CAN bus (UAVCAN/DroneCAN) | Future-proofing for CAN ESCs or GPS modules. Board has CAN hardware. | High | Not needed for FPV acro. Defer entirely. |
| Servo outputs (S1=PE6, S2=PE5 via TIM15) | PX4 supports mixed motor+servo configs. Useful for tilt-rotor or camera gimbal later. | Low-Med | TIM15CH1 and TIM15CH2. Declare in board_config. Not needed for quad; include for completeness if upstreaming. |
| I2C1 magnetometer support | GPS connector (UART7) shares with I2C1 for mag. PX4 mag support requires HMC5883 or similar driver. | Low | Wiring exists; just not bringing up in v1. Leave I2C1 declared in NuttX for later. |
| QGroundControl sensor calibration workflow | Not a code feature — but validated end-to-end QGC connection with working sensor data is the acceptance criterion for v1. | Low | This is validation work, not dev work. |
| `px4_metadata` / parameter metadata for board | Upstream PRs benefit from board-specific parameter defaults (e.g., default DSHOT speed, IMU rotation). | Low | Encode in `board.cmake` or `init.d` startup script. Polish item for upstream PR. |

---

## Anti-Features

Things to deliberately NOT build or enable in v1. Scope creep here causes delays without flight benefit.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| MAX7456 OSD (SPI3) | PX4 doesn't use analog OSD. The MAX7456 is irrelevant to PX4 stack. Enabling SPI3 for OSD wastes development time and creates DMA contention risk. | Leave SPI3 unconfigured or disabled in NuttX defconfig. |
| GPS / magnetometer bring-up | v1 is FPV acro. GPS adds positioning modes that require weeks of additional calibration and parameter tuning. Scope explodes. | Declare UART7 and I2C1 pins in NuttX config (for future use), but don't enable GPS drivers or modes in `default.cmake`. |
| UAVCAN / DroneCAN | CAN stack adds 50+ KB flash, significant config complexity, and zero benefit for FPV acro. | Leave CAN peripheral unconfigured. |
| Dual-camera switching / video routing | Entirely outside PX4's domain. | Ignore. |
| iNav / Betaflight compatibility | Different firmware stacks, different boot protocols, different storage layouts. PX4 will overwrite iNav when flashed. Don't try to maintain dual-boot. | PX4-only from day one of this project. |
| Advanced PX4 modes (Loiter, RTL, Auto mission) | These require GPS + mag + full EKF2 stack. They will fail without GPS. Attempting to enable them introduces confusing failure modes during v1 bringup. | Disable in QGC flight mode config. Only test Stabilized and Acro. |
| Custom PX4 estimator tuning | EKF2 default params work for initial flight validation. Custom tuning is post-flight work. | Fly with defaults first; tune only after stable hover is confirmed. |

---

## Feature Dependencies

```
NuttX board config
  └─> board_config.h (pin assignments)
        └─> ICM-42688 SPI driver instances (both)
        └─> DPS310 I2C driver instance
        └─> UART assignments (3,6,7,8)
        └─> ADC VBAT/CURR channels
        └─> LED pins
        └─> USB detect pin

NuttX board config
  └─> Timer config (TIM2/3/4/5 for motors)
        └─> DSHOT output (unidirectional first)
              └─> Bidirectional DSHOT (RPM filter) [DEFERRED]

DSHOT output
  └─> Actuator output config / mixer
        └─> QGroundControl arming and motor test

ICM-42688 (at least one healthy) + DPS310
  └─> PX4 arming checks pass
        └─> Stabilized mode flight validation

USB MAVLink / console
  └─> QGroundControl connection
        └─> Sensor calibration
        └─> Flight mode configuration

CMakeLists.txt + default.cmake
  └─> CI compilation pass
        └─> Upstream PR accepted
```

---

## Specific Technical Notes

### ICM-42688-P Driver (HIGH confidence)

The `icm42688p` driver has been in PX4 mainline since approximately PX4 v1.13 (2022). It supports both ICM-42688-P and ICM-42688-V variants via the same driver.

Registration pattern in `board_config.h`:
```c
#define PX4_SPI_BUS_SENSORS  1  // SPI1 for Gyro 1
#define PX4_SPI_BUS_SENSORS2 4  // SPI4 for Gyro 2

// Gyro 1 (SPI1, CS=PA4, DRDY=PC3, rotation CW270 = ROTATION_YAW_270)
#define PX4_ICM42688P_1 {.spi_dev = PX4_SPIDEV_ICM42688P, .drdy_gpio = GPIO_EXTI_ICM42688P_DRDY1, ...}

// Gyro 2 (SPI4, CS=PE11, DRDY=PE10, rotation CW180 = ROTATION_YAW_180)
#define PX4_ICM42688P_2 {.spi_dev = PX4_SPIDEV_ICM42688P2, .drdy_gpio = GPIO_EXTI_ICM42688P_DRDY2, ...}
```

The exact macro names vary by PX4 version — use the Matek H743 Slim `board_config.h` as the definitive template.

### DPS310 Driver (HIGH confidence)

DPS310 driver (`dps310`) exists in PX4 mainline. The board uses I2C2 at address 0x77.

Declaration in board startup or `board_config.h`:
```c
#define PX4_I2C_BUS_EXPANSION 2  // I2C2 for baro
#define DPS310_I2C_BUS  PX4_I2C_BUS_EXPANSION
#define DPS310_I2C_ADDR 0x77
```

The DPS310 can also be wired to SPI on some boards, but the Orqa uses I2C — the I2C driver path applies.

### DSHOT Motor Output (MEDIUM confidence — most complex)

PX4 DSHOT on STM32H7 uses the `dshot` output driver with DMA-based TIM channel capture/compare. Key constraints:

- Each DSHOT channel requires a dedicated DMA stream
- STM32H743 has DMAMUX which provides flexible DMA routing, reducing conflicts vs F7
- DSHOT300 is the standard for most FPV ESCs (including Orqa ESC3030 per project context)
- DSHOT600 is possible on H7 but less common in PX4 configs

Timer allocation for Orqa (from Betaflight config):
```
TIM4 CH1/CH2 → M1 (PD12), M2 (PD13)
TIM2 CH2/CH1 → M3 (PA1),  M4 (PA0)   [note: TIM2 channel order may vary]
TIM5 CH3/CH4 → M5 (PA2),  M6 (PA3)
TIM3 CH4/CH3 → M7 (PB1),  M8 (PB0)
```

DMA stream assignments must be verified against the Matek H743 Slim reference — conflicts between DSHOT DMA and SPI DMA (for IMU) are the most common bringup failure.

The `io_timer_channel_allocation` table in NuttX `stm32h7_tim.c` must list all 8 channels with correct DMA requests via DMAMUX.

### MAVLink / USB Console (HIGH confidence)

PX4 exposes MAVLink over USB-CDC by default. Requirements:
- NuttX USB CDC/ACM driver enabled in defconfig
- `PA9` USB detect pin declared (already in Betaflight config / PROJECT.md)
- `SERIAL_USB` enabled in PX4 module config
- No additional driver work — this is infrastructure, not board-specific

QGroundControl connects to USB at 115200 or auto-baud. No board-specific configuration needed beyond the above.

### Upstream PR Requirements (MEDIUM confidence — based on PX4 contribution history)

Based on patterns from recent STM32H7 board PRs merged into PX4 main:

1. **Compilation in CI** — PR must pass `px4_fmu-v6x` and related CI checks. Board-specific CI check added automatically once `boards/` entry exists.
2. **No new compiler warnings** — H743 builds must be warning-clean at `-Wall -Wextra`.
3. **Maintainer identified** — PX4 now requires a named maintainer in `MAINTAINERS.md` or similar. For community ports, the submitter is listed.
4. **Flight test evidence** — PRs for new board targets are typically expected to show logs or video of the board running PX4 before merge. This is informal but consistently expected.
5. **README / docs stub** — A minimal `.rst` or `.md` in `docs/` describing the board (pinout, features, where to buy). Not mandatory to block merge but strongly expected.
6. **No vendored binary blobs** — All code must be open source / compile from source.
7. **Board `default.cmake` must list only real supported modules** — Don't enable GPS, CAN, or other unvalidated modules in the upstreamed config.

---

## MVP Recommendation

For v1 (first flight), prioritize strictly:

1. NuttX board config + `board_config.h` (boots to NuttX shell)
2. USB MAVLink / console (can interact with QGC)
3. ICM-42688 primary gyro (sensor data visible in QGC)
4. DPS310 barometer (altitude data visible)
5. DSHOT output 8 channels unidirectional (motors spin on command)
6. UART3 (RC receiver input — essential for manual flight)
7. ADC VBAT (battery monitoring — PX4 won't arm without it)
8. Fly in Stabilized mode

Defer to post-first-flight:
- Second ICM-42688 (reduce complexity during initial bringup; add after first flight)
- Bidirectional DSHOT / RPM notch filter
- W25Q128 flash / blackbox
- Beeper
- Servo outputs
- Upstream PR polish (maintainer docs, parameter defaults)

---

## Sources

- PX4 source knowledge through training cutoff August 2025 (HIGH confidence for established features)
- Matek H743 Slim as reference target (community-proven, similar MCU/peripheral layout)
- STM32H743 datasheet / DMA/timer peripheral knowledge (HIGH confidence)
- PROJECT.md hardware description and Betaflight pin assignments (authoritative for this board)
- PX4 upstream contribution patterns from merged PRs ~2022-2025 (MEDIUM confidence — informal requirements may have evolved)
- NOTE: No live web verification was possible in this session. ICM-42688 driver existence and DPS310 driver existence are HIGH confidence from training data, but exact macro names and file structure should be verified against current PX4 main branch before implementation.
