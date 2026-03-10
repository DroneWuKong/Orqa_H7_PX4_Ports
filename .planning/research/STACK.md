# Technology Stack

**Project:** PX4 Port — Orqa H7 QuadCore (STM32H743)
**Researched:** 2026-03-10
**Research mode:** Ecosystem (training data only — all external tools denied in this session)

> **IMPORTANT CAVEAT:** All web search, WebFetch, and Bash tool access was denied during this research
> session. Every finding below is drawn from training data (knowledge cutoff ~August 2025). The PX4
> toolchain and NuttX configuration format evolve steadily — verify versions against the live PX4 main
> branch before acting. Specific version numbers are flagged with their confidence level.

---

## Recommended Stack

### Compiler & Toolchain

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| arm-none-eabi-gcc | 12.x or 13.x (see note) | Cross-compiler for Cortex-M7 | PX4's CI ships a specific pinned version; using it avoids subtle code-gen divergence | MEDIUM — verify current pinned version in `Tools/setup/ubuntu.sh` in the PX4 repo |
| CMake | 3.22+ | Meta-build system | PX4 requires CMake 3.22+ as of v1.14; STM32H7 builds use CMake for board discovery | HIGH |
| Ninja | 1.11+ | Build backend | PX4 defaults to Ninja over Make; faster incremental builds | HIGH |
| Python 3 | 3.8–3.11 | Build scripts, upload tools | PX4 build scripts and `px4_sitl` use Python; 3.11 is safe as of 2024 | HIGH |
| pip packages | per `requirements.txt` | PX4 toolchain support | `empy`, `jinja2`, `pyserial`, `pyyaml` — pin to repo's requirements.txt | HIGH |
| Docker / px4io/px4-dev-nuttx | current | Hermetic build env | px4-dev-nuttx Docker image gives the exact compiler PX4 CI uses; eliminates "works on my machine" | HIGH |

**Pinning the compiler:** PX4 pins `arm-none-eabi-gcc` to a specific Launchpad release inside
`Tools/setup/ubuntu.sh`. Do NOT use the system package manager's `gcc-arm-none-eabi` — it may be
a different minor version and produce different flash layout or FPU behaviour. Pull the pinned URL
from that script before building.

### RTOS & HAL

| Technology | Version | Purpose | Why | Confidence |
|------------|---------|---------|-----|------------|
| NuttX | PX4-bundled (do not use upstream NuttX independently) | RTOS providing POSIX-like API | PX4 ships its own NuttX fork at `platforms/nuttx/NuttX/`; diverges from upstream | HIGH |
| STM32H7 NuttX BSP | in-tree | HAL for STM32H7xx peripherals | NuttX's STM32H7 architecture support is mature; covers SPI, I2C, UART, DMA, TIM | HIGH |
| PX4 NuttX layer | in-tree | Thin glue between NuttX + PX4 drivers | `src/drivers/` PX4 driver layer sits on top of NuttX device files | HIGH |

### Build System Files (what you create for a new board)

| File / Directory | Location | Purpose | Confidence |
|-----------------|----------|---------|------------|
| Board `CMakeLists.txt` | `boards/VENDOR/BOARD/CMakeLists.txt` | Declares board name, MCU, driver modules to include | HIGH |
| `default.px4board` | `boards/VENDOR/BOARD/default.px4board` | Kconfig-style feature flags (was formerly `default.cmake`) | HIGH |
| `nuttx-config/` directory | `boards/VENDOR/BOARD/nuttx-config/` | All NuttX .config, defconfig, and Kconfig overrides | HIGH |
| `nuttx-config/nsh/defconfig` | above | Main NuttX defconfig for the board's NSH shell configuration | HIGH |
| `nuttx-config/bootloader/defconfig` | above | Bootloader variant defconfig (PX4 bootloader is separate project) | MEDIUM |
| `init.d/` scripts | `boards/VENDOR/BOARD/init.d/` | Startup scripts (mixer loading, parameter defaults) | HIGH |
| `src/` (optional) | `boards/VENDOR/BOARD/src/` | Board-specific C++ code: `board_config.h`, `init.c`, optional custom drivers | HIGH |

### Reference Board to Copy From

| Reference | Why | Risk |
|-----------|-----|------|
| `boards/matek/h743-slim/` | Same STM32H743 MCU, community-proven PX4 port, similar peripheral count and UART assignment style | LOW — structural risk is low; pin differences require careful diffing |
| `boards/holybro/kakuteh7/` | Another H743 FPV-oriented board in PX4 tree; useful cross-reference for DSHOT timer config | LOW |
| `boards/cuav/x7pro/` | Industrial H7 target; good for understanding H743 DMA configuration | MEDIUM — quite different peripheral set |

**Recommendation:** Copy `matek/h743-slim` as the base, then diff against `kakuteh7` for DSHOT/FPV
specifics. The Matek H743 Slim is explicitly identified in the project's key decisions as the basis.

### Key Source Files in Reference Board

| File | What to Learn From It | Confidence |
|------|----------------------|------------|
| `boards/matek/h743-slim/src/board_config.h` | All GPIO pin assignments using PX4's `GPIO_*` macros; SPI CS pin definitions; UART numbering | HIGH |
| `boards/matek/h743-slim/nuttx-config/nsh/defconfig` | NuttX kernel options, SPI/I2C/UART enablement, DMA channel assignments | HIGH |
| `boards/matek/h743-slim/CMakeLists.txt` | Which PX4 driver modules are included (ICM-42688, DPS310, etc.) | HIGH |
| `boards/matek/h743-slim/default.px4board` | Kconfig feature flags: DSHOT, UAVCAN, logging, etc. | HIGH |

### Driver Modules (pre-existing in PX4, just need to include)

| Driver | PX4 Module Name | Interface | Notes | Confidence |
|--------|-----------------|-----------|-------|------------|
| ICM-42688-P | `drivers/imu/invensense/icm42688p` | SPI | In PX4 main as of ~v1.13; supports dual instances | HIGH |
| DPS310 | `drivers/barometer/dps310` | I2C or SPI | I2C address 0x77 matches board spec | HIGH |
| DSHOT ESC | `drivers/dshot` | TIM+DMA | PX4 supports DSHOT300/600; bidir DSHOT support added ~v1.14 | MEDIUM — verify bidir status |
| W25Q128 flash | `drivers/mtd/flashiap` or `at24xx`-equivalent | SPI | PX4 uses MTD layer; W25Q128 likely covered under `ramtron` or similar SPI NOR driver | LOW — verify exact PX4 driver for W25Q128FV |
| SD card (SDMMC) | `drivers/sdcard` | SDMMC | STM32H743 has SDMMC1; standard PX4 support | HIGH |
| USB CDC-ACM | `drivers/cdc_acm_serial` | USB FS/HS | PX4 standard USB console/MAVLink | HIGH |
| ADC (VBAT/CURR) | `drivers/adc` | ADC | Standard PX4 ADC driver; maps channels via `board_config.h` | HIGH |
| PWM/Servo | `drivers/pwm_out` | TIM | Needed for S1/S2 servo outputs; shares timer infrastructure with DSHOT | HIGH |
| Beeper | `drivers/tone_alarm` | TIM | PX4 tone alarm driver | HIGH |

### NuttX Configuration Key Concepts

| Concept | Detail | Confidence |
|---------|--------|------------|
| `defconfig` format | KConfig-format text file; controls which NuttX subsystems compile in | HIGH |
| DMA channel assignment | STM32H7 uses DMAMUX; NuttX assigns channels in `stm32h7_dma.h`; conflicts cause silent failures | HIGH |
| SPI device numbering | NuttX SPI buses are 1-indexed; PX4 maps them in `board_config.h` with `PX4_SPI_BUS_*` macros | HIGH |
| Clock tree | HSE 8MHz → PLL1 → 480MHz sysclk; this matches the board spec; `nuttx-config` must set `STM32H7_HSE_FREQUENCY=8000000` | HIGH |
| Flash/RAM layout | STM32H743 has 2MB flash (dual bank), 1MB DTCM+AXI RAM; NuttX linker script must match | HIGH |
| ITCM vs DTCM | Time-critical code (gyro ISR) should be in ITCM; PX4 handles placement via `__attribute__((section))` | MEDIUM |

### Build Commands

| Task | Command | Notes |
|------|---------|-------|
| Configure build | `make orqa_h7quadcore_default` (once board exists) | Board name follows `VENDOR_BOARD_CONFIG` pattern |
| Initial reference build | `make matek_h743-slim_default` | Verify toolchain works before porting |
| Build + upload via USB | `make matek_h743-slim_default upload` | Requires PX4 bootloader on target |
| menuconfig for NuttX | `make matek_h743-slim_default boardconfig` | Launches NuttX KConfig menu; useful for diffing |
| Clean | `make clean` | Clean before switching targets |
| Build in Docker | `docker run --rm -v $PWD:/src px4io/px4-dev-nuttx:latest bash -c "cd /src && make matek_h743-slim_default"` | Hermetic build |

### PX4 Bootloader

| Item | Detail | Confidence |
|------|--------|------------|
| Repository | `PX4/PX4-Bootloader` (separate repo from PX4-Autopilot) | HIGH |
| Purpose | USB DFU / UART upload of firmware; lives in first 32KB of flash | HIGH |
| Board config | Bootloader also has board-specific configs; a new board target may need a bootloader port | MEDIUM — can often use an existing H743 bootloader binary for initial bringup |
| Upload tool | `px_uploader.py` in PX4-Autopilot tools; also `dfu-util` for DFU | HIGH |
| Alternative initial flash | STM32CubeProgrammer or `st-flash` (OpenOCD) via SWD for first-time flashing | HIGH |

### Debug & Flashing Hardware

| Tool | Purpose | Why | Confidence |
|------|---------|-----|------------|
| ST-LINK v2 / v3 | SWD debug probe | Standard for STM32; required for initial board bring-up without bootloader | HIGH |
| OpenOCD | GDB server for SWD debug | Works with ST-LINK; PX4 ships OpenOCD configs for some targets | HIGH |
| STM32CubeProgrammer | GUI flash tool from ST | Useful for initial bootloader flashing; handles BOOT0 pin mode | HIGH |
| J-Link (optional) | Higher-speed SWD probe | Better for live debugging; more expensive | MEDIUM |
| SWD pinout | STM32H743 SWD: SWDIO=PA13, SWCLK=PA14 (standard ARM SWD) | These pins are dedicated on STM32H7 | HIGH |

### Ground Control & Validation

| Tool | Purpose | Confidence |
|------|---------|------------|
| QGroundControl | Parameter tuning, sensor calibration, MAVLink status | HIGH |
| mavlink-inspector (QGC built-in) | Verify MAVLink messages from board | HIGH |
| `nsh>` shell over USB | Direct NuttX shell for driver bring-up (e.g., `icm42688p start`) | HIGH |
| `listener` command in NSH | PX4 uORB topic monitoring from shell | HIGH |
| PX4 log analysis (FlightPlot/PX4 Logs) | Post-flight validation | HIGH |

---

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| Compiler source | PX4-pinned ARM GCC from Launchpad | System `apt` gcc-arm-none-eabi | Different minor versions; PX4 CI pins exact version; mismatches cause FPU/ABI issues |
| Build environment | Docker px4-dev-nuttx | Native Ubuntu install | Native is fine for experienced devs, but Docker eliminates Python/tool version drift |
| Reference board | `matek/h743-slim` | `holybro/kakuteh7` | Matek H743 Slim is closer in peripheral layout; already identified as project basis |
| Bidir DSHOT | PX4 DSHOT driver with bidir | Separate ESC telemetry UART | Board has both options; bidir DSHOT is preferred for FPV to reduce wiring |
| Flash logging | W25Q128 via SPI NOR MTD | SD card only | Board has both; SPI flash is faster for blackbox; SD for full logs — use both |

---

## Critical Version Pins (VERIFY BEFORE USE)

These are known-correct as of my training data but MUST be re-verified against the live PX4 main branch:

| Item | Training-data value | Where to verify |
|------|--------------------|--------------------|
| arm-none-eabi-gcc version | 12.3.Rel1 (Launchpad) | `Tools/setup/ubuntu.sh` in PX4-Autopilot main |
| CMake minimum version | 3.22 | `CMakeLists.txt` root of PX4-Autopilot |
| NuttX version bundled | 10.4.x (PX4 fork) | `platforms/nuttx/NuttX/` git submodule |
| px4board format | KConfig (replaced old .cmake) | Any existing H7 board's `default.px4board` |
| Python minimum | 3.8 | `Tools/setup/ubuntu.sh` or CI config |

---

## Directory Structure for New Board Target

```
boards/
  orqa/                              ← new vendor directory
    h7quadcore/                      ← new board directory
      CMakeLists.txt                 ← board declaration, module list
      default.px4board               ← Kconfig feature flags
      board.cmake                    ← (may be auto-generated or minimal)
      src/
        board_config.h               ← ALL GPIO, SPI, I2C, UART pin macros
        init.c                       ← board_app_initialize(), peripheral power-up
        CMakeLists.txt               ← builds src/ files
      nuttx-config/
        nsh/
          defconfig                  ← main NuttX config (900+ lines, copy+modify from matek)
          Kconfig                    ← (sometimes empty/minimal)
        bootloader/
          defconfig                  ← bootloader NuttX config
      init.d/
        rcS                          ← PX4 startup script
        (rc.board_extras)            ← optional board-specific startup additions
```

**Vendor name:** The project should register as `orqa` vendor. If upstreaming, this creates
`boards/orqa/` which is a new vendor entry in the PX4 tree. Ensure the vendor name matches
the company's standard — check if `orqa` is already present in any PX4 branch.

---

## Installation

```bash
# Option 1: Native Ubuntu 22.04 (recommended for daily development)
git clone https://github.com/PX4/PX4-Autopilot.git --recursive
cd PX4-Autopilot
bash Tools/setup/ubuntu.sh          # Installs pinned arm-gcc + Python deps

# Option 2: Docker (recommended for first build / CI parity)
docker pull px4io/px4-dev-nuttx:latest
docker run --rm -it -v $(pwd):/src px4io/px4-dev-nuttx:latest bash

# Verify reference build works first
make matek_h743-slim_default

# After board files created:
make orqa_h7quadcore_default
```

---

## What NOT To Do

| Anti-pattern | Why | Instead |
|--------------|-----|---------|
| Use system `apt` gcc-arm-none-eabi | Version mismatch with PX4's pinned compiler; causes subtle FPU/ABI bugs | Use `Tools/setup/ubuntu.sh` or Docker |
| Start from scratch instead of copying Matek H743 Slim | The defconfig has 900+ lines; the `board_config.h` GPIO macro format is non-trivial | Copy, then surgically modify |
| Modify NuttX source files directly | Changes get wiped on submodule update; breaks upstreaming | Use defconfig overrides and `board_config.h` |
| Use `default.cmake` format | Deprecated; replaced by `.px4board` KConfig format | Use `default.px4board` |
| Enable all drivers in CMakeLists.txt | Bloats flash; STM32H743 has 2MB but PX4 builds can exceed 1.5MB with too many modules | Include only what the board uses |
| Skip the SWD debug probe | Can't recover a bad flash without it; BOOT0 mode + CubeProgrammer is a backup but slower | Have ST-LINK v2 ready before first flash |
| Assume DMA channel assignments are automatic | STM32H7 DMAMUX requires explicit channel assignment in defconfig; conflicts cause silent peripheral failures | Diff DMA assignments from Matek defconfig carefully |

---

## Sources

**Confidence note:** All sources below are from training data. No live web access was available
during this research session. Verify against current main branch before acting.

- PX4 Developer Guide: https://docs.px4.io/main/en/hardware/porting_guide.html
- PX4 GitHub board targets: https://github.com/PX4/PX4-Autopilot/tree/main/boards/
- Matek H743-Slim reference: https://github.com/PX4/PX4-Autopilot/tree/main/boards/matek/h743-slim/
- Holybro KakuteH7 reference: https://github.com/PX4/PX4-Autopilot/tree/main/boards/holybro/kakuteh7/
- PX4 NuttX porting: https://docs.px4.io/main/en/hardware/porting_guide_nuttx.html
- PX4 Dev Setup: https://docs.px4.io/main/en/dev_setup/dev_env.html
- STM32H743 Reference Manual: RM0433 (ST Microelectronics) — DMA, TIM, SPI chapters
- PX4-Bootloader repo: https://github.com/PX4/PX4-Bootloader
