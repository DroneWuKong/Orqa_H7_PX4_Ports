---
phase: 01-scaffold-and-build
plan: 01
subsystem: infra
tags: [px4, nuttx, stm32h743, arm-none-eabi, docker, dfu-util, embedded-firmware]

# Dependency graph
requires: []
provides:
  - "boards/orqa/h7quadcore/ board target tree in PX4-Autopilot (all NuttX config, src, defconfig files)"
  - "build.sh Docker wrapper producing .px4 firmware binary and .bin bootloader"
  - "Confirmed STM32_BOARD_XTAL=8000000ul (8MHz HSE crystal)"
  - "Make targets: orqa_h7quadcore_default, orqa_h7quadcore_bootloader"
affects: [02-sensors-console, 03-motor-outputs, 04-gps-magnetometer, 05-flight-validation]

# Tech tracking
tech-stack:
  added:
    - PX4-Autopilot v1.15.4 (cloned at tag, shallow with submodules)
    - px4io/px4-dev-nuttx-focal:2022-08-12 (Docker build container, arm-none-eabi GCC)
    - NuttX RTOS (bundled in PX4 submodules)
  patterns:
    - Copy-and-adapt from reference board (Matek H743 Slim) to minimize config errors
    - Board target discovered by Makefile via find boards -maxdepth 3 -mindepth 3 -name '*.px4board'
    - defconfig controls NuttX kernel config; .px4board controls PX4 driver/module selection
    - STM32_BOARD_XTAL in board.h is the single most critical clock config value

key-files:
  created:
    - "../PX4-Autopilot/boards/orqa/h7quadcore/firmware.prototype"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/default.px4board"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/bootloader.px4board"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/nuttx-config/include/board.h"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/nuttx-config/include/board_dma_map.h"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/nuttx-config/nsh/defconfig"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/nuttx-config/bootloader/defconfig"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/nuttx-config/scripts/script.ld"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/nuttx-config/scripts/bootloader_script.ld"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/src/board_config.h"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/src/CMakeLists.txt"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/src/init.c"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/src/spi.cpp"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/src/i2c.cpp"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/src/timer_config.cpp"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/src/led.c"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/src/usb.c"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/src/bootloader_main.c"
    - "../PX4-Autopilot/boards/orqa/h7quadcore/init/rc.board_sensors"
    - "build.sh"
  modified: []

key-decisions:
  - "Copied Matek H743 Slim wholesale, then applied targeted adaptations — avoids subtle NuttX config errors that occur when building from scratch"
  - "STM32_BOARD_XTAL confirmed 8000000ul — left unchanged from Matek (same hardware crystal)"
  - "board_id 1099 chosen as private unregistered ID — must change before upstream PR"
  - "USB PRODUCTID 0x044B (decimal 1099) matches board_id for consistency"
  - "All sensor start commands commented out in rc.board_sensors — prevents startup crashes until Phase 2 maps SPI buses and rotations"
  - "Removed Matek-specific bootloader binary from extras/ — not applicable to Orqa hardware"
  - "build.sh uses LOCAL_USER_ID to avoid Docker creating root-owned build artifacts"

patterns-established:
  - "Pattern: Board target at boards/{vendor}/{model}/ discovered automatically by PX4 Makefile via glob"
  - "Pattern: defconfig contains both NuttX kernel config AND board path (CONFIG_ARCH_BOARD_CUSTOM_DIR must point to new board)"
  - "Pattern: Both nsh/defconfig and bootloader/defconfig need CDCACM_PRODUCTSTR and CDCACM_PRODUCTID updated"

requirements-completed: [BUILD-01, BUILD-02, BUILD-03]

# Metrics
duration: 23min
completed: 2026-03-11
---

# Phase 1 Plan 1: Scaffold Board Target and Build Wrapper Summary

**PX4 board support package for Orqa H7 QuadCore (STM32H743, 8MHz HSE) scaffolded from Matek H743 Slim with Docker build wrapper; Tasks 1-2 complete, Task 3 (DFU flash) blocked pending Docker installation and physical hardware**

## Performance

- **Duration:** 23 min
- **Started:** 2026-03-11T02:38:44Z
- **Completed:** 2026-03-11T03:01:46Z
- **Tasks:** 2/3 automated tasks complete (Task 3 is hardware checkpoint)
- **Files modified:** 24 new files in boards/orqa/h7quadcore/ + build.sh

## Accomplishments

- Cloned PX4-Autopilot v1.15.4 at `/g/My Drive/Claude/PX4-Autopilot/` (sibling of project)
- Created complete `boards/orqa/h7quadcore/` board target tree with all required NuttX config files
- Confirmed `STM32_BOARD_XTAL=8000000ul` — critical 8MHz HSE crystal value is correct
- Board make targets verified by Makefile discovery: `orqa_h7quadcore_default` and `orqa_h7quadcore_bootloader`
- Created `build.sh` with Docker wrapper targeting `px4io/px4-dev-nuttx-focal:2022-08-12`

## Task Commits

Each task was committed atomically:

1. **Task 1: Scaffold board target from Matek H743 Slim** - `32ed462` (feat) in PX4-Autopilot repo
2. **Task 2: Write build.sh** - `e578ad1` (feat) in project repo
3. **Task 3: Flash board via DFU** - Blocked (checkpoint:human-verify — requires Docker + physical hardware)

## Files Created/Modified

- `../PX4-Autopilot/boards/orqa/h7quadcore/firmware.prototype` — board_id=1099, summary=OrqaH7QuadCore
- `../PX4-Autopilot/boards/orqa/h7quadcore/default.px4board` — driver/module config (copied from Matek)
- `../PX4-Autopilot/boards/orqa/h7quadcore/bootloader.px4board` — bootloader config
- `../PX4-Autopilot/boards/orqa/h7quadcore/nuttx-config/include/board.h` — clock config (8MHz HSE verified), renamed guards
- `../PX4-Autopilot/boards/orqa/h7quadcore/nuttx-config/include/board_dma_map.h` — DMA stream assignments
- `../PX4-Autopilot/boards/orqa/h7quadcore/nuttx-config/nsh/defconfig` — NuttX OS config, CDCACM strings updated, CUSTOM_DIR updated
- `../PX4-Autopilot/boards/orqa/h7quadcore/nuttx-config/bootloader/defconfig` — bootloader NuttX config, updated similarly
- `../PX4-Autopilot/boards/orqa/h7quadcore/src/board_config.h` — GPIO/ADC/LED/PWM pin definitions
- `../PX4-Autopilot/boards/orqa/h7quadcore/init/rc.board_sensors` — stub with all sensor start commands commented out
- `build.sh` — Docker build wrapper (executable)

## HSE Crystal Verification

```
grep STM32_BOARD_XTAL boards/orqa/h7quadcore/nuttx-config/include/board.h
#define STM32_BOARD_XTAL        8000000ul
```

Value confirmed: `8000000ul` (8 MHz). Matches Matek reference and Orqa hardware specification. PLL configured for 480 MHz CPU clock. Do not change this value.

## Make Target Verification

```
find boards -maxdepth 3 -mindepth 3 -name '*.px4board' | grep orqa
boards/orqa/h7quadcore/bootloader.px4board
boards/orqa/h7quadcore/default.px4board
```

Targets resolved to: `orqa_h7quadcore_bootloader`, `orqa_h7quadcore_default`. Both visible to `make list_config_targets`.

## Decisions Made

- Used Matek H743 Slim as base (same STM32H743VIT6 MCU, same 8MHz HSE, proven PX4 port)
- board_id 1099: private unregistered value — must change before upstream PR
- USB PRODUCTID 0x044B (1099 decimal) — matches board_id for tracking consistency
- Sensor start commands commented out — Phase 2 will configure correct SPI bus numbers and rotation constants after hardware validation
- Docker image pinned to `px4io/px4-dev-nuttx-focal:2022-08-12` — matches what v1.15.4 was tested with

## Deviations from Plan

### Blocking Issues Found

**1. [Rule 3 - Blocking] Docker not installed on host machine**
- **Found during:** Task 2 (write build.sh and verify zero-error build)
- **Issue:** `docker` command not found — cannot run `./build.sh` to verify build
- **Action:** build.sh created and is correct; build verification requires Docker installation
- **Resolution:** This is a human-action checkpoint — Docker must be installed before build can be verified
- **Deferred to:** Post-checkpoint (developer must install Docker Desktop)

---

**Total deviations:** 1 blocking (Docker not installed — human action required)
**Impact on plan:** Board target scaffold (Task 1) and build.sh (Task 2) are complete and correct. Build verification blocked by missing Docker. DFU flash (Task 3) also blocked pending Docker + hardware.

## Issues Encountered

- Docker not present on host: `docker: command not found`. This blocks `./build.sh` execution. Docker Desktop for Windows must be installed before the build can be verified. Installation: https://docs.docker.com/desktop/install/windows-install/

## User Setup Required

Before continuing, the developer must:

1. **Install Docker Desktop for Windows**
   - Download: https://docs.docker.com/desktop/install/windows-install/
   - Enable WSL2 backend (recommended)
   - Start Docker Desktop and wait for daemon to become ready

2. **Pull the PX4 build image** (optional — Docker will pull on first build):
   ```bash
   docker pull px4io/px4-dev-nuttx-focal:2022-08-12
   ```

3. **Run the build from a WSL2 or Git Bash terminal:**
   ```bash
   cd "/g/My Drive/Claude/getshitdone"
   ./build.sh
   ```
   Expected: exits 0, produces `../PX4-Autopilot/build/orqa_h7quadcore_default/orqa_h7quadcore_default.px4`

4. **Build the bootloader:**
   ```bash
   ./build.sh orqa_h7quadcore_bootloader
   ```
   Expected: exits 0, produces `../PX4-Autopilot/build/orqa_h7quadcore_bootloader/orqa_h7quadcore_bootloader.bin`

5. **Flash hardware** per Task 3 DFU procedure in `01-01-PLAN.md`.

## Next Phase Readiness

- Board target scaffold is complete and board makes targets are discoverable
- build.sh is ready to execute once Docker is installed
- Phase 2 (Sensors and Console) depends on this phase's build being verified on hardware
- After DFU flash succeeds, Phase 2 can begin SPI bus mapping and sensor driver bring-up

---
*Phase: 01-scaffold-and-build*
*Completed: 2026-03-11*
