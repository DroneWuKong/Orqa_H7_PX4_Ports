# Architecture Patterns

**Domain:** PX4 STM32H743 board target (NuttX RTOS, FPV quadcopter)
**Project:** PX4 Port — Orqa H7 QuadCore
**Researched:** 2026-03-10
**Confidence note:** Research tools (WebSearch, WebFetch, Bash, GitHub CLI) were all denied in this session. This document is based on training data (knowledge cutoff August 2025) of the PX4 codebase, which is stable and well-documented for board target structure. Confidence: MEDIUM-HIGH. Verify key file content against `boards/matek/h743-slim` in the actual PX4 repo before writing code.

---

## Recommended Architecture

A PX4 board target is a thin hardware description layer sitting between the generic PX4 stack and the NuttX RTOS. The board target does NOT contain flight logic — it only maps hardware.

```
PX4 Application Layer  (flight stack, MAVLink, estimators)
         |
PX4 Platform Layer     (drivers, uORB, POSIX-like API)
         |
Board Target Layer     boards/orqa/h7quadcore/
         |
NuttX RTOS             platforms/nuttx/NuttX/
         |
STM32H743 Hardware
```

### Component Boundaries

| Component | Responsibility | Communicates With |
|-----------|---------------|-------------------|
| `CMakeLists.txt` | Declares which PX4 modules/drivers to include in the build | CMake build system, all module CMakeLists |
| `default.px4board` | KConfig feature flags — what is enabled/disabled | `menuconfig` / `px4board` tooling |
| `nuttx-config/` | NuttX kernel config (defconfig) and peripheral config (include/) | NuttX build system |
| `nuttx-config/include/board.h` | Pin/clock/DMA/timer hardware definitions for NuttX drivers | All NuttX peripheral drivers |
| `init.d-posix/` or `rcS` / `rc.board_sensors` | Runtime startup script — mounts FS, starts drivers, loads params | NuttX init system (NSH shell) |
| `src/` | Board-specific C++ code: `board_config.h`, `init.c`, optional `canbus.cpp` | PX4 platform layer |

---

## Directory Structure

Reference structure from `boards/matek/h743-slim` (basis target):

```
boards/
  orqa/
    h7quadcore/
      CMakeLists.txt                  # Module list for the build
      default.px4board                # KConfig feature selection
      init.d/                         # NuttX NSH startup scripts
        rcS                           # Root startup script (usually minimal, calls platform)
        rc.board_sensors              # Sensor startup: starts drivers by name
        rc.board_defaults             # Default parameter overrides for this board
      nuttx-config/
        h7quadcore/                   # Config name matches build target
          defconfig                   # Full NuttX kernel configuration
        include/
          board.h                     # Pin definitions, clocks, DMA, timer mappings
      src/
        CMakeLists.txt                # Builds board-specific C sources
        board_config.h                # PX4-layer hardware constants (SPI CSs, EXTI pins)
        init.c                        # board_app_initialize(), LED init, USB detect
        canbus.cpp                    # (optional) CAN bus initialization
      romfs/
        px4fmu_common/                # (optional) files baked into ROM filesystem
```

The `nuttx-config/h7quadcore/` subdirectory name must exactly match the `-b` argument used with `make px4_fmu-v6c_default` — for a new target it becomes `orqa_h7quadcore_default`.

---

## Key Files: Detail

### 1. `CMakeLists.txt` (top-level board CMakeLists)

The central manifest. Controls what compiles into the firmware image.

Structure:
```cmake
px4_add_board(
  PLATFORM nuttx
  VENDOR orqa
  MODEL h7quadcore
  LABEL default
  TOOLCHAIN arm-none-eabi
  ARCHITECTURE cortex-m7
  CONSTRAINED_FLASH

  DRIVERS
    adc/board_adc
    barometer/dps310
    distance_sensor         # (omit if not used)
    dshot
    imu/invensense/icm42688p
    magnetometer            # (deferred — v1 scope)
    mounted_orientation
    osd                     # (omit — MAX7456 not used in PX4)
    pwm_out
    tone_alarm

  MODULES
    attitude_estimator_q
    commander
    ekf2
    flight_mode_manager
    land_detector
    logger
    mavlink
    mc_att_control
    mc_pos_control
    mc_rate_control
    navigator
    sensors

  SYSTEMCMDS
    bl_update
    dmesg
    led_control
    mixer
    motor_test
    param
    perf
    pwm
    reboot
    reflect
    sd_bench
    serial_passthru
    top
    topic_listener
    tune_control
    uorb
    ver
    work_queue
)
```

Key points:
- `DRIVERS` lists driver module paths relative to `src/drivers/`
- `dshot` enables the DSHOT driver (replaces `pwm_out` for motor control — both are often listed; DSHOT is selected at runtime by mixer/actuator config)
- Omit GPS, magnetometer, optical flow drivers for v1 scope
- The `imu/invensense/icm42688p` driver handles both ICM-42688-P gyros; two instances are started from `rc.board_sensors`

### 2. `default.px4board` (KConfig)

Selects high-level features. Minimal content for a new target:

```kconfig
CONFIG_BOARD_CONSTRAINED_FLASH=y
CONFIG_DRIVERS_IMU_INVENSENSE_ICM42688P=y
CONFIG_DRIVERS_BAROMETER_DPS310=y
CONFIG_DRIVERS_DSHOT=y
CONFIG_DRIVERS_PWM_OUT=y
CONFIG_MODULES_EKF2=y
CONFIG_MODULES_MC_RATE_CONTROL=y
```

This is auto-generated by `make orqa_h7quadcore menuconfig` and should not be hand-edited after initial creation. Start from the Matek H743 Slim `default.px4board` and prune/add as needed.

### 3. `nuttx-config/h7quadcore/defconfig`

Full NuttX kernel configuration. This is the longest and most complex file. It configures:
- STM32H7 clock tree (HSE=8MHz → PLL → 480MHz SYSCLK)
- UART instances (which are enabled, baud rates)
- SPI buses (bus numbers, DMA channels)
- I2C buses
- USB (OTG FS on PA11/PA12)
- SD card (SDMMC1)
- DMA controller allocation

**Critical STM32H743 constraint:** The H743 has two DMA controllers (DMA1, DMA2) and one MDMA. SPI/UART assignments must avoid DMA channel conflicts. The Matek H743 Slim defconfig is the correct starting point — only change lines that differ in pin assignments or peripheral enables.

Key `defconfig` lines for this board:
```
CONFIG_STM32H7_HSE_FREQUENCY=8000000
CONFIG_STM32H7_SPI1=y       # ICM-42688 gyro 1
CONFIG_STM32H7_SPI2=y       # W25Q128 flash
CONFIG_STM32H7_SPI3=y       # MAX7456 OSD (even if unused, keep to avoid GPIO conflict)
CONFIG_STM32H7_SPI4=y       # ICM-42688 gyro 2
CONFIG_STM32H7_USART3=y     # UART3: VTx/receiver
CONFIG_STM32H7_UART7=y      # UART7: GPS connector
CONFIG_STM32H7_USART6=y     # UART6: SIK telemetry
CONFIG_STM32H7_UART8=y      # UART8: ESC telemetry
CONFIG_STM32H7_I2C2=y       # DPS310 baro
CONFIG_STM32H7_SDMMC1=y     # SD card
CONFIG_STM32H7_OTG_FS=y     # USB
```

### 4. `nuttx-config/include/board.h`

The hardware pin map. This is the file most likely to require careful adaptation from the Matek H743 Slim.

Structure (relevant sections):

**Clock:**
```c
#define STM32_BOARD_XTAL        8000000ul   // 8MHz HSE crystal
#define STM32_HSE_FREQUENCY     STM32_BOARD_XTAL
// PLL configuration to reach 480MHz
#define STM32_PLLCFG_PLL1CFG    (RCC_PLLCFGR_PLL1SRC_HSE | ...)
```

**UART pin assignments** (NuttX uses GPIO_UARTn_TX / GPIO_UARTn_RX macros):
```c
// UART3 — VTx / RC receiver
#define GPIO_USART3_TX          GPIO_USART3_TX_2    // PD8
#define GPIO_USART3_RX          GPIO_USART3_RX_2    // PD9

// UART6 — SiK telemetry
#define GPIO_USART6_TX          GPIO_USART6_TX_1    // PC6
#define GPIO_USART6_RX          GPIO_USART6_RX_1    // PC7

// UART7 — GPS connector
#define GPIO_UART7_TX           GPIO_UART7_TX_2     // PE8
#define GPIO_UART7_RX           GPIO_UART7_RX_2     // PE7

// UART8 — ESC telemetry
#define GPIO_UART8_TX           GPIO_UART8_TX_1     // PE1
#define GPIO_UART8_RX           GPIO_UART8_RX_1     // PE0
```

The `_1`, `_2` suffixes are alternate function remapping indices defined in NuttX's `stm32h7x3xx_pinmap.h` — look up which index maps to which physical pin for the H743.

**SPI chip selects** (not in board.h — these go in `src/board_config.h`):
```c
// board_config.h (PX4 layer, not NuttX layer)
#define PX4_SPI_BUS_SENSORS         1   // SPI1 — gyro 1
#define PX4_SPI_BUS_SENSORS2        4   // SPI4 — gyro 2
#define PX4_SPI_BUS_BARO            2   // (baro is I2C, not SPI)
#define PX4_SPI_BUS_MEMORY          2   // SPI2 — flash

#define GPIO_SPI1_CS_ICM42688_1     /* PA4 — gyro 1 CS */
#define GPIO_SPI4_CS_ICM42688_2     /* PE11 — gyro 2 CS */
#define GPIO_SPI2_CS_MEMORY         /* PB12 — flash CS */
```

**EXTI (data-ready interrupts for IMUs):**
```c
// In board_config.h
#define GPIO_DRDY_ICM42688_1        /* PC3 — gyro 1 DRDY */
#define GPIO_DRDY_ICM42688_2        /* PE10 — gyro 2 DRDY */
```

**Timer/PWM for motors** (board.h, DMA section):
```c
// TIM4 CH1/CH2 → M1(PD12), M2(PD13)
// TIM2 CH2/CH1 → M3(PA1), M4(PA0)
// TIM5 CH3/CH4 → M5(PA2), M6(PA3)
// TIM3 CH4/CH3 → M7(PB1), M8(PB0)
#define DIRECT_PWM_OUTPUT_CHANNELS  8
```

### 5. `init.d/rc.board_sensors`

NSH script that starts sensor drivers at boot. This is PX4 shell script syntax (not bash).

```bash
#!/bin/sh
# Orqa H7 QuadCore sensor init

# ICM-42688 — gyro 1 on SPI1, CS=PA4, DRDY=PC3
icm42688p start -s -R 6 -b 1 -c 0
# -s = SPI
# -R 6 = rotation 6 (CW270 = ROTATION_YAW_270)
# -b 1 = SPI bus 1
# -c 0 = chip select index 0 (first CS on bus)

# ICM-42688 — gyro 2 on SPI4, CS=PE11, DRDY=PE10
icm42688p start -s -R 4 -b 4 -c 0
# -R 4 = rotation 4 (CW180 = ROTATION_YAW_180)
# -b 4 = SPI bus 4

# DPS310 barometer on I2C2 addr 0x77
dps310 start -X -b 2 -a 0x77
# -X = external I2C (I2C2 is treated as "external" in PX4 topology)
# -b 2 = I2C bus 2

# ADC (battery voltage/current)
adc start
```

**Rotation constants** (map Betaflight alignment to PX4 ROTATION enum):
- CW270 → `ROTATION_YAW_270` = 6
- CW180 → `ROTATION_YAW_180` = 4

Verify enum values against `src/lib/matrix/matrix/Dcm.hpp` or `lib/ecl/geo/geo.h`.

### 6. `init.d/rc.board_defaults`

Parameter overrides specific to this board. Loaded after default params.

```bash
#!/bin/sh
# Orqa H7 QuadCore board defaults

param set-default SENS_BOARD_ROT 0      # no board rotation in PX4 (handled per-sensor)
param set-default BAT1_V_DIV 11.1       # Voltage scale from Betaflight: 112/1/12 → 12.1ish; calibrate on bench
param set-default BAT1_A_PER_V 36.0    # Current sensor scale (108 in Betaflight; convert)
param set-default DSHOT_CONFIG 300      # DSHOT300
param set-default MOT_ORDERING 0        # Standard motor ordering
```

---

## Data Flow

### Sensor Data Flow

```
IMU hardware (ICM-42688)
  → SPI DMA transfer (NuttX SPI driver)
  → icm42688p driver (PX4 driver layer)
  → publishes sensor_accel / sensor_gyro uORB topics
  → EKF2 / attitude estimator consumes
  → vehicle_attitude / vehicle_angular_velocity topics
  → mc_rate_control → actuator_controls
  → mixer → actuator_outputs
  → PWM/DSHOT output driver → ESC
```

### Motor Output Data Flow

```
mc_rate_control → actuator_controls uORB
  → mixer (airframe config in /etc/mixers/)
  → actuator_outputs uORB
  → dshot driver (or pwm_out driver)
  → TIM4/TIM2/TIM5/TIM3 timers via DMA
  → motor signal on PD12/PD13/PA1/PA0/PA2/PA3/PB1/PB0
```

### UART Assignment in NuttX/PX4

```
defconfig enables STM32H7_USARTn → NuttX creates /dev/ttySn device
  → rc.board_sensors / mavlink start assigns purpose:
    /dev/ttyS0 → MAVLink (USB virtual serial, typically)
    /dev/ttyS2 → UART3 (VTx / RC receiver)
    /dev/ttyS5 → UART6 (SiK telemetry)
    /dev/ttyS6 → UART7 (GPS)
    /dev/ttyS7 → UART8 (ESC telemetry bidir DSHOT)
```

The `ttySn` numbering is determined by the order UARTs are listed in the NuttX board serial config — it does NOT directly correspond to UART number. Verify against the `nsh_romfsimg.h` or by inspecting Matek H743 Slim's serial console output.

---

## How Sensor Drivers Are Registered

PX4 uses a driver start-from-script model, not an auto-probe model.

1. The driver module is compiled in via `CMakeLists.txt` DRIVERS list.
2. The driver is enabled in `default.px4board` KConfig.
3. At boot, `rc.board_sensors` calls `drivername start [args]` in the NSH shell.
4. The driver registers itself with the uORB system and begins publishing.

For two instances of the same driver (dual ICM-42688):
- Call `icm42688p start` twice with different `-b` (bus) and `-c` (CS) arguments.
- PX4 assigns instance numbers automatically (instance 0, instance 1).
- EKF2 can be configured to use both instances via `SENS_IMU_MODE` parameter.

---

## How DSHOT/PWM Output Is Configured

### Architecture

```
actuator_outputs topic
  → Output driver (dshot OR pwm_out, selected by DSHOT_CONFIG param)
    → Timer HAL (platform/nuttx/src/px4_nuttx_impl.cpp)
      → STM32 TIM registers via DMA
        → Physical pins
```

### Timer Configuration

In `board.h` (NuttX layer), timers are declared with their DMA channels:

```c
/* Timer DMA map — must not conflict with SPI/UART DMA */
#define DMAMAP_TIM4_UP    DMAMAP_DMA1_TIM4UP_0   // M1, M2
#define DMAMAP_TIM2_UP    DMAMAP_DMA1_TIM2UP_0   // M3, M4
#define DMAMAP_TIM5_UP    DMAMAP_DMA1_TIM5UP_0   // M5, M6
#define DMAMAP_TIM3_UP    DMAMAP_DMA1_TIM3UP_0   // M7, M8
```

DMA stream conflicts are the most common source of silent failures on STM32H7. The H743 has 8 streams per DMA controller — verify no two peripherals share a stream.

### DSHOT Selection

DSHOT is enabled at runtime (not compile time) via:
```
param set DSHOT_CONFIG 300   # or 150, 600
```

When `DSHOT_CONFIG > 0`, the `dshot` driver takes over motor output. The timer pins must still be configured identically to PWM — only the output waveform changes.

For DSHOT bidirectional (telemetry feedback):
```
param set DSHOT_BIDIR_EN 1
```
Bidirectional DSHOT requires the timer pin to be capable of both output and capture — all STM32H7 TIM channels are.

### Mixer / Actuator Config

For multirotor, the mixer is selected via:
```
param set SYS_AUTOSTART 4001   # generic quadcopter X
```
Motor ordering follows PX4 convention (front-right CCW = motor 1). If the Orqa board's physical motor positions differ, adjust `CA_ROTORn_*` actuator configuration parameters or use a custom mixer.

---

## How UARTs Are Mapped in NuttX

### Two-Layer Mapping

**Layer 1: NuttX defconfig** — which UART hardware is enabled:
```
CONFIG_STM32H7_USART3=y
CONFIG_STM32H7_USART3_SERIALDRIVER=y
```

**Layer 2: NuttX serial order** — which `/dev/ttySn` number is assigned:
The order is determined by `CONFIG_STM32H7_USART*` definitions in the defconfig and the serial port ordering list in the NuttX board serial header. Typically:
- ttyS0 = USART1 (or the first enabled UART)
- ttyS1 = USART2
- etc.

This is NOT alphabetical — it follows the enable sequence in the board serial config. The Matek H743 Slim maps are the correct reference.

**Layer 3: PX4 purpose assignment** — in `rc.board_sensors` and startup scripts:
```bash
mavlink start -d /dev/ttyS2 -b 57600    # telemetry port
```

### UART Port Table for Orqa H7 QuadCore

| Board Label | STM32 UART | Pins | ttySn* | Intended Use |
|------------|-----------|------|--------|--------------|
| UART3 | USART3 | PD8/PD9 | ttyS2 | VTx / RC receiver (CRSF/SBUS) |
| UART6 | USART6 | PC6/PC7 | ttyS5 | SiK telemetry / MAVLink |
| UART7 | UART7 | PE8/PE7 | ttyS6 | GPS (deferred v1) |
| UART8 | UART8 | PE1/PE0 | ttyS7 | ESC telemetry |

*ttySn numbers are approximate — verify against Matek H743 Slim serial console. The actual mapping depends on defconfig UART enable order.

---

## Patterns to Follow

### Pattern 1: Copy-then-Diff from Matek H743 Slim

**What:** Copy the entire `boards/matek/h743-slim` directory to `boards/orqa/h7quadcore`, rename config directory, then diff each file against hardware specs.

**When:** Always — never create a board target from scratch on H743.

**Why:** The Matek H743 Slim `defconfig` contains hundreds of validated NuttX config lines. Getting clock/DMA/SPI config right from scratch on STM32H7 takes weeks. The diff between Matek and Orqa is ~30 lines.

**Process:**
```
1. Copy boards/matek/h743-slim → boards/orqa/h7quadcore
2. Rename nuttx-config/h743-slim → nuttx-config/h7quadcore
3. Update all references to "matek", "h743-slim" → "orqa", "h7quadcore"
4. Diff board.h pin assignments vs PROJECT.md hardware table
5. Diff CMakeLists.txt vs desired driver list
6. Diff rc.board_sensors vs sensor bus/CS/rotation values
```

### Pattern 2: Sensor Driver Start with Explicit Bus+CS

**What:** Always specify `-b` (bus number) and `-c` (CS index) explicitly in `rc.board_sensors`, never rely on defaults.

**When:** Always, on any board with multiple SPI buses.

**Why:** Default CS selection silently maps to wrong device when multiple buses are present. Explicit args make the mapping auditable.

### Pattern 3: Verify DMA Map Before Uncommenting Peripherals

**What:** Before enabling SPI2 (flash), verify its DMA stream doesn't conflict with TIM DMA or UART DMA in `defconfig`.

**When:** Any time adding a new peripheral to defconfig.

**Why:** STM32H7 DMA conflicts produce no error — the peripheral simply doesn't work or corrupts data. This is the most common hardware bring-up failure mode on H743.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Editing `defconfig` by Hand at Scale

**What:** Manually adding 50+ KConfig lines to defconfig.
**Why bad:** Missing dependencies cause cryptic NuttX build failures; KConfig has inter-option dependencies that `menuconfig` handles automatically.
**Instead:** Use `make orqa_h7quadcore menuconfig` to generate defconfig after initial copy.

### Anti-Pattern 2: Changing Timer DMA Without Checking Whole Map

**What:** Reassigning a DMA stream for a timer without auditing all other DMA users.
**Why bad:** Silent conflict — motor output silently broken, or SPI DMA corrupted.
**Instead:** Build and review the full DMA allocation table in `defconfig` before any timer change.

### Anti-Pattern 3: Wrong Sensor Rotation

**What:** Using default rotation (0) for sensors that are physically rotated.
**Why bad:** The quadcopter will not stabilize correctly; may not be immediately obvious in bench tests.
**Instead:** Confirm rotation from Betaflight config (`align_gyro = CW270FLIP` etc.) and map to PX4 ROTATION enum before first flight. Test with stationary sensor data in QGroundControl.

### Anti-Pattern 4: Skipping USB Console Validation

**What:** Proceeding to sensor bringup without first validating that NSH console works over USB.
**Why bad:** Without NSH access, sensor driver failures produce no visible output and are nearly impossible to diagnose.
**Instead:** First build milestone: get USB console → `nsh>` prompt → `uname -a` before touching sensors.

### Anti-Pattern 5: Enabling All Drivers at Once

**What:** Compiling 20 drivers in CMakeLists.txt and starting all from rc.board_sensors on first boot.
**Why bad:** Any one failing driver can hang the init sequence; root cause is ambiguous.
**Instead:** Start with minimal driver set (USB, one IMU, no sensors). Add and validate one driver at a time.

---

## Suggested Build Order

This order minimizes debugging surface at each step:

### Step 1: Scaffold (Copy + Rename)
Copy Matek H743 Slim. Update all name references. Confirm `make orqa_h7quadcore_default` runs CMake without errors. No firmware flash yet.

### Step 2: Minimal Build (Boots to NSH)
- Strip CMakeLists.txt to absolute minimum (no sensors, no GPS)
- Verify clock config in defconfig matches 8MHz HSE → 480MHz
- Flash and verify USB console → NSH prompt
- Deliverable: `nsh> uname -a` returns STM32H743 target name

### Step 3: LEDs + ADC
- Wire LED1(PA8), LED2(PA11), LED3(PD11) in board_config.h / init.c
- Enable ADC for VBAT(PC0), CURR(PC1)
- Deliverable: LEDs blink, `adc test` shows battery voltage

### Step 4: First IMU (Gyro 1)
- Enable icm42688p driver for SPI1 bus 1
- Wire CS=PA4, DRDY=PC3 in board_config.h
- Set rotation CW270 in rc.board_sensors
- Deliverable: `icm42688p status` shows sensor data, QGC shows IMU

### Step 5: Second IMU (Gyro 2)
- Add second icm42688p instance on SPI4 bus 4, CS=PE11, DRDY=PE10
- Set rotation CW180
- Deliverable: Both IMUs show in QGC sensor tab

### Step 6: Barometer
- Enable dps310 driver for I2C2
- Deliverable: `dps310 status` shows pressure/temperature

### Step 7: UARTs
- Enable UART3, UART6, UART7, UART8 in defconfig
- Verify ttyS assignments with loopback test
- Start MAVLink on telemetry UART
- Deliverable: QGC connects over SiK telemetry

### Step 8: Motor Outputs
- Add DSHOT driver, configure timer DMA in defconfig
- Set DSHOT_CONFIG=300 parameter
- Verify with `motor_test` (props OFF)
- Deliverable: All 8 motors spin in sequence

### Step 9: SD Card + Logging
- SDMMC1 already likely enabled from Matek config
- Deliverable: `ls /fs/microsd` works, flight logging enabled

### Step 10: Integration + First Flight
- Set SYS_AUTOSTART=4001 (quadcopter X)
- Calibrate sensors (accel, gyro, level)
- Arming checks pass in QGC
- Deliverable: Flies in Stabilized mode

---

## Scalability Considerations

This is an embedded firmware target — scalability means firmware size and CPU headroom:

| Concern | Current State | Risk | Mitigation |
|---------|--------------|------|------------|
| Flash usage | STM32H743 has 2MB flash; typical PX4 build is ~1.3MB | LOW | Remove unused modules from CMakeLists.txt |
| CPU headroom | 480MHz Cortex-M7; EKF2 + dual IMU uses ~40% | LOW | Monitor `top` output; H743 has plenty |
| RAM | 1MB DTCM + AXI SRAM; PX4 uses ~500KB | LOW | Check `free` in NSH if adding heavy modules |
| DMA contention | 8 streams per DMA controller, shared by SPI+UART+TIM | MEDIUM | Map all DMA users before enabling flash/SPI3 |

---

## Sources

- Training data knowledge of PX4-Autopilot source (codebase structure stable since 2019) — MEDIUM confidence
- PX4 developer documentation on board porting (https://docs.px4.io/main/en/hardware/porting_guide.html) — not fetched (tool denied); HIGH confidence that this URL is valid and contains porting guide
- Matek H743 Slim as basis target (https://github.com/PX4/PX4-Autopilot/tree/main/boards/matek/h743-slim) — not fetched; verify file contents directly before coding
- Betaflight config `betaflight_4.4.1_STM32H743_ORQAH7QUADCORE.zip` — pin assignments in PROJECT.md taken from this
- PX4 STM32H7 NuttX defconfig conventions — MEDIUM confidence (stable area, many H743 targets follow same pattern)

**Validation required before coding:** Fetch actual `boards/matek/h743-slim/` file tree and compare each file section against this document. Particularly: ttyS UART numbering order, DMA stream assignments, and icm42688p start command flags (verify `-R` rotation values against current PX4 source).
