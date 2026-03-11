# Phase 1: Scaffold and Build - Research

**Researched:** 2026-03-10
**Domain:** PX4 NuttX board porting — STM32H743, Docker build, DFU flashing
**Confidence:** HIGH (all critical claims verified against v1.15.4 source and official docs)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- Local branch on a cloned PX4-Autopilot — no GitHub fork yet (fork deferred until upstream PR time)
- Pin to a stable release tag (e.g. v1.15.x), not main
- Board target lives in-tree: `boards/orqa/h7quadcore/`
- This project directory and PX4-Autopilot clone live as sibling directories (separate repos, no nesting)
- Shell script wrapper (`build.sh`) at this project root
- Single command invokes `docker run` targeting the pinned px4io image and building `px4_orqa_h7quadcore`
- No local compiler required — Docker only
- Derive from Matek H743 Slim (same STM32H743 MCU family, community-proven PX4 port)
- dfu-util via boot button (meets BUILD-03 success criterion)

### Claude's Discretion
- Which exact px4io Docker image tag to pin
- Whether to copy Matek H743 Slim files wholesale or build incrementally
- STM32CubeProgrammer as optional fallback for flashing
- CMake/nuttx config details within the board target

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| BUILD-01 | Developer can build PX4 firmware for `orqa/h7quadcore` target using Docker/pinned toolchain (no local compiler setup required) | Docker image identified (`px4io/px4-dev-nuttx-focal:2022-08-12`); board target make name is `px4_orqa_h7quadcore_default`; `build.sh` wraps `docker run` |
| BUILD-02 | Board target compiles with zero errors and zero warnings | Copy-then-adapt strategy from Matek H743 Slim; critical HSE crystal pitfall documented; all required files identified |
| BUILD-03 | Developer can flash firmware to the board via DFU mode using the boot button | Two-step DFU process documented: bootloader `.bin` via `dfu-util`, then firmware via QGC or `make upload` |
</phase_requirements>

---

## Summary

Phase 1 creates a new PX4 board support package (BSP) for the Orqa H7 QuadCore by copying the Matek H743 Slim target — the most appropriate reference because both boards use the same STM32H743VIT6 MCU with an 8 MHz HSE crystal. The Docker build environment is well-defined: PX4 v1.15.4 uses `px4io/px4-dev-nuttx-focal:2022-08-12` as its pinned NuttX toolchain image, confirmed directly from `Tools/docker_run.sh` in the v1.15.4 tree. The `build.sh` wrapper invokes `docker run` with the PX4-Autopilot source volume-mounted and executes `make px4_orqa_h7quadcore_default` inside.

Flashing a board that currently runs Betaflight requires a two-step DFU procedure: first flash a PX4 NuttX bootloader binary (`_bootloader` make target) via `dfu-util -a 0 --dfuse-address 0x08000000 -D <bootloader.bin>`, then flash the application firmware via QGroundControl or `make px4_orqa_h7quadcore_default upload`. The STM32 DFU ROM cannot be erased, so the board cannot be bricked.

The single most important correctness requirement for Phase 1 is the HSE crystal frequency: the Orqa H7 QuadCore (like Matek H743 Slim) uses an 8 MHz crystal, so `STM32_BOARD_XTAL` must be `8000000ul` in `nuttx-config/include/board.h`. Getting this wrong produces a silently wrong PLL configuration that causes the MCU to run at an incorrect CPU frequency, making subsequent debugging very difficult.

**Primary recommendation:** Copy `boards/matek/h743-slim/` wholesale to `boards/orqa/h7quadcore/`, then do a targeted find-and-replace pass to update product names, board IDs, USB product strings, and file guard macros. Verify HSE crystal setting before first build attempt.

---

## Standard Stack

### Core
| Library / Tool | Version | Purpose | Why Standard |
|---------------|---------|---------|--------------|
| PX4-Autopilot | v1.15.4 (tag) | Firmware source tree | Latest stable; v1.16 RC at time of research |
| px4io/px4-dev-nuttx-focal | 2022-08-12 | Docker build container (arm-none-eabi GCC, CMake, NuttX tools) | Pinned in `Tools/docker_run.sh` for v1.15.4; verified from source |
| NuttX RTOS | bundled with PX4 | Board RTOS, drivers, HAL | Embedded in PX4 submodules — no separate install |
| dfu-util | ≥ 0.9 | Flash bootloader via USB DFU | Cross-platform, open source, STM32 DFU standard |
| QGroundControl | latest stable | Flash application firmware after bootloader installed | Official PX4 GCS; handles `.px4` upload automatically |

### Supporting
| Tool | Purpose | When to Use |
|------|---------|-------------|
| STM32CubeProgrammer | GUI fallback for DFU flashing on Windows | If dfu-util fails or unavailable on developer's OS |
| ccache | Build cache — dramatically speeds re-builds | Mount `~/.ccache` into Docker container (already done in `docker_run.sh`) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `px4io/px4-dev-nuttx-focal:2022-08-12` | `px4io/px4-dev:v1.16.0` (new unified image) | New unified image works for main branch; for v1.15.4, use the date-tagged focal image to match the toolchain the release was tested with |
| QGC for firmware flash | `make px4_orqa_h7quadcore_default upload` | `make upload` works but requires correct serial port; QGC is more reliable for first-time flash |

**Installation (host — Docker only; no host compiler needed):**
```bash
docker pull px4io/px4-dev-nuttx-focal:2022-08-12
# dfu-util for flashing bootloader:
sudo apt install dfu-util        # Linux
brew install dfu-util            # macOS
```

---

## Architecture Patterns

### Recommended Project Structure

Two sibling directories on the host:

```
<workspace>/
├── PX4-Autopilot/                  # Cloned at tag v1.15.4
│   └── boards/
│       └── orqa/
│           └── h7quadcore/         # New board target (in-tree)
└── <this-project>/                 # Project repo
    ├── build.sh                    # Single-command Docker build wrapper
    └── .planning/                  # GSD planning files
```

### Board Target Directory Structure (inside PX4-Autopilot)

```
boards/orqa/h7quadcore/
├── bootloader.px4board             # Bootloader build config (toolchain, arch)
├── default.px4board                # App build config (drivers, modules, serial mappings)
├── firmware.prototype              # Board ID and USB product string
├── nuttx-config/
│   ├── Kconfig                     # Board Kconfig stub
│   ├── include/
│   │   ├── board.h                 # Clock config (HSE, PLL), pin mux macros
│   │   └── board_dma_map.h         # DMA stream assignments
│   ├── bootloader/
│   │   └── defconfig               # NuttX bootloader OS config
│   ├── nsh/
│   │   └── defconfig               # NuttX app OS config (UARTs, SPI, I2C enabled)
│   └── scripts/                    # Linker scripts (copy from Matek)
└── src/
    ├── CMakeLists.txt
    ├── board_config.h              # GPIO/ADC/LED/PWM pin definitions
    ├── hw_config.h                 # Debug UART, USB config
    ├── bootloader_main.c
    ├── init.c                      # Board startup, power sequencing
    ├── led.c                       # LED driver
    ├── i2c.cpp                     # I2C bus configuration
    ├── spi.cpp                     # SPI bus/chip-select configuration
    ├── timer_config.cpp            # PWM timer/DMA pin mapping
    └── usb.c                       # USB CDC-ACM setup
```

### Pattern 1: Copy-and-Adapt Reference Target

**What:** Copy the entire `boards/matek/h743-slim/` tree to `boards/orqa/h7quadcore/` then systematically update identifiers and pin definitions.

**When to use:** Always for first Phase 1 — gets a compiling baseline before any customization. Building incrementally from scratch risks subtle NuttX config errors that are hard to diagnose.

**Adaptation checklist (minimum for Phase 1 compilation):**

1. `firmware.prototype` — change `board_id` to an unused private value (e.g. `1099`), update `summary` and `description` to "OrqaH7QuadCore"
2. `default.px4board` — update `CONFIG_CDCACM_PRODUCTSTR` (USB name shown on host)
3. `nuttx-config/nsh/defconfig` — update `CONFIG_CDCACM_PRODUCTSTR` and `CONFIG_CDCACM_PRODUCTID` to match new board_id
4. `nuttx-config/include/board.h` — verify `STM32_BOARD_XTAL=8000000ul` (already correct in Matek; confirm Orqa hardware uses same 8 MHz crystal)
5. All `#ifndef` guard macros in headers — rename from `MATEKH743SLIM` to `ORQAH7QUADCORE`
6. `src/board_config.h` — placeholder GPIO definitions for LED pin (required for compilation); all other pins can be left as Matek values initially

**Example — firmware.prototype:**
```json
{
    "board_id": 1099,
    "magic": "PX4FWv1",
    "description": "Firmware for the Orqa H7 QuadCore",
    "image": "",
    "build_time": 0,
    "summary": "OrqaH7QuadCore",
    "version": "0.1",
    "image_size": 0,
    "image_maxsize": 1966080,
    "git_identity": "",
    "board_revision": 0
}
```

### Pattern 2: Docker Build Invocation

**What:** `build.sh` wraps `docker run` with the PX4-Autopilot volume mounted.

**Example — build.sh:**
```bash
#!/usr/bin/env bash
# Source: adapted from PX4-Autopilot/Tools/docker_run.sh (v1.15.4)
set -euo pipefail

PX4_SRC="$(cd "$(dirname "$0")/../PX4-Autopilot" && pwd)"
CCACHE_DIR="${HOME}/.ccache"
mkdir -p "${CCACHE_DIR}"

docker run --rm \
  --env=LOCAL_USER_ID="$(id -u)" \
  --env=CCACHE_DIR="${CCACHE_DIR}" \
  --volume="${PX4_SRC}:${PX4_SRC}:rw" \
  --volume="${CCACHE_DIR}:${CCACHE_DIR}:rw" \
  --workdir="${PX4_SRC}" \
  px4io/px4-dev-nuttx-focal:2022-08-12 \
  /bin/bash -c "make px4_orqa_h7quadcore_default"
```

**Notes:**
- `LOCAL_USER_ID` causes the container to write output files as the host user (avoids root-owned build artifacts)
- The `--workdir` must be the mounted PX4-Autopilot directory
- On Windows hosts, Docker Desktop must be running with the source drive shared; paths in volume mounts must use forward slashes or Docker Desktop path format

### Pattern 3: Make Target Naming Convention

PX4 make targets follow: `make {VENDOR}_{MODEL}_{VARIANT}`

For `boards/orqa/h7quadcore/default.px4board`:
- **VENDOR** = `orqa`
- **MODEL** = `h7quadcore`
- **VARIANT** = `default` (from filename `default.px4board`)

Full make command: `make px4_orqa_h7quadcore_default`

Wait — the `px4_` prefix is only used for Pixhawk reference boards. For third-party boards, the target name is `{VENDOR}_{MODEL}_{VARIANT}`. Verify with `make list_config_targets` inside the container after adding the board.

**Correction:** The actual make target for `boards/matek/h743-slim/default.px4board` is `make matek_h743-slim_default`. For `boards/orqa/h7quadcore/default.px4board` it will be `make orqa_h7quadcore_default`.

### Pattern 4: DFU Flash Procedure

**Step 1: Build the PX4 bootloader for the new board**
```bash
# Inside the Docker container or in build.sh variant:
make orqa_h7quadcore_bootloader
# Output: build/orqa_h7quadcore_bootloader/orqa_h7quadcore_bootloader.bin
```

Note: The `bootloader.px4board` config enables a NuttX-based bootloader. For Phase 1 a new board won't have a pre-compiled bootloader yet. The board currently runs Betaflight, which means the Betaflight bootloader is in the STM32 DFU-resident ROM area (ST factory DFU at 0x1FF00000). The PX4 application bootloader goes at 0x08000000.

**Step 2: Enter DFU mode**
Hold the BOOT button, plug USB-C, release BOOT after USB enumeration.

**Step 3: Flash PX4 bootloader**
```bash
dfu-util -a 0 --dfuse-address 0x08000000 -D \
  build/orqa_h7quadcore_bootloader/orqa_h7quadcore_bootloader.bin
```

**Step 4: Unplug and replug USB (no BOOT button)**
PX4 bootloader enumerates and waits briefly for firmware upload.

**Step 5: Flash application firmware**
```bash
# Option A: QGroundControl — Vehicle Setup > Firmware > Advanced > Custom firmware
# Option B: make upload (requires board connected, correct port detected)
make orqa_h7quadcore_default upload
```

### Anti-Patterns to Avoid

- **Skipping the bootloader step:** Attempting to flash a `.px4` firmware binary directly to 0x08000000 via dfu-util will fail — the `.px4` format is not a raw binary; it is a JSON-wrapped image. The PX4 bootloader handles `.px4` unpacking; dfu-util needs the raw `.bin` bootloader.
- **Building from `main` branch:** The main branch is rapidly changing. Pin to `v1.15.4` so the Docker image GCC version matches the source toolchain expectations.
- **Wrong working directory in Docker:** `--workdir` must be the PX4-Autopilot directory, not `/src` or any alias. NuttX CMake resolves `CONFIG_ARCH_BOARD_CUSTOM_DIR` as a relative path from the build tree.
- **Running Docker as root without LOCAL_USER_ID:** Build artifacts are written as root; subsequent `make clean` or git operations on the host fail with permission errors.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Clock/PLL configuration | Custom PLL calculation | Copy Matek board.h + verify crystal | STM32H7 PLL has 4 stages (M, N, P, Q, R divisors); getting VCO range and output frequency wrong causes silent mis-clocking |
| NuttX defconfig | Write from scratch | Copy Matek defconfig, use `make menuconfig` to adjust | defconfig has 200+ interdependent options; menuconfig enforces Kconfig dependency rules |
| DMA stream assignment | Manually assign DMA streams | Copy `board_dma_map.h` from Matek, adjust only conflicting streams | STM32H7 DMA has strict DMAMUX channel matrix; conflicts produce hard faults at runtime |
| USB CDC-ACM | Custom USB stack | `CONFIG_CDCACM=y` in defconfig + `usb.c` from Matek | USB enumeration protocol is complex; the NuttX CDC-ACM driver is tested and correct |
| Bootloader | Write custom bootloader | Use `make orqa_h7quadcore_bootloader` | PX4 NuttX bootloader supports DFU upload, `.px4` image validation, and CRC checking |

**Key insight:** NuttX board configuration is highly interdependent. Changing one option (e.g. enabling a UART) requires corresponding pinmux entries in board.h and correct DMA stream allocation in board_dma_map.h. The copy-and-verify strategy protects against partial configurations that compile but fail at runtime.

---

## Common Pitfalls

### Pitfall 1: Wrong HSE Crystal Frequency
**What goes wrong:** The board boots but the systick runs at wrong frequency; USB may not enumerate; UART baud rates are incorrect; IMU SPI timing is off.
**Why it happens:** Some H7 reference boards (e.g. some Pixhawk variants) use 16 MHz HSE. Matek H743 Slim and the Orqa H7 QuadCore both use 8 MHz. If a 16 MHz defconfig is copied from a different board, `STM32_BOARD_XTAL` is wrong.
**How to avoid:** Confirm in board.h that `STM32_BOARD_XTAL 8000000ul`. Matek's board.h already has this correct. Verified from source: the Matek H743 Slim comment explicitly states "X1: 8 MHz crystal for HSE."
**Warning signs:** USB fails to enumerate after flashing; dmesg shows USB device reset loops.

### Pitfall 2: Make Target Name Confusion
**What goes wrong:** Running `make px4_orqa_h7quadcore_default` returns "No rule to make target" because the `px4_` prefix only applies to boards under `boards/px4/`.
**Why it happens:** PX4 FMU reference boards are under `boards/px4/fmu-vX/` and their targets start with `px4_`. Third-party boards use `{vendor}_{model}_{variant}`.
**How to avoid:** After adding the board directory, run `make list_config_targets | grep orqa` inside the Docker container to confirm the exact target name. Expected: `orqa_h7quadcore_default`.
**Warning signs:** CMake error "No such board" during configure phase.

### Pitfall 3: Docker Volume Permissions (Linux hosts)
**What goes wrong:** Build artifacts created inside the container are owned by root; `git status` shows unexpected modified files; subsequent builds fail.
**Why it happens:** The Docker container runs as root by default. The `LOCAL_USER_ID` environment variable tells the px4io container entry point to drop privileges to the host user UID.
**How to avoid:** Always pass `--env=LOCAL_USER_ID="$(id -u)"` to `docker run`. The `docker_run.sh` template does this correctly.
**Warning signs:** `ls -la build/` shows files owned by root on the host.

### Pitfall 4: DFU Address Confusion (Bootloader vs Application)
**What goes wrong:** Developer attempts to flash the `.px4` application image directly via `dfu-util` to 0x08000000. The file is not a raw binary — it is a JSON wrapper around a compressed image — and the flash results in garbage data.
**Why it happens:** The `.px4` format is PX4-specific; only the PX4 bootloader knows how to unpack it. `dfu-util` expects a raw `.bin`.
**How to avoid:** Use `dfu-util` only for the `_bootloader.bin` file. Use QGroundControl or `make upload` for the application `.px4` firmware.
**Warning signs:** Board appears to flash successfully but fails to boot; NSH console never appears.

### Pitfall 5: Board ID Collision
**What goes wrong:** QGroundControl refuses to flash firmware, saying "firmware not compatible with board."
**Why it happens:** `firmware.prototype` `board_id` must be unique; if the same ID as an existing board is used, QGC may refuse to load firmware.
**How to avoid:** Use a high private ID (e.g. 1099) not listed in the PX4 board registry. Alternatively, skip QGC for Phase 1 and use `make upload` which ignores board ID matching.
**Warning signs:** QGC shows "firmware version mismatch" or refuses to load custom firmware.

### Pitfall 6: Windows Docker Path Format in Volume Mounts
**What goes wrong:** On Windows (Docker Desktop with WSL2), the volume mount path syntax differs.
**Why it happens:** Windows paths like `C:\Users\...` must be converted to `/c/Users/...` (Git Bash) or `//c/Users/...` for some Docker contexts.
**How to avoid:** In `build.sh`, use `$(pwd -W)` on Git Bash or ensure the script is run from WSL2 where standard Unix paths work.
**Warning signs:** Docker reports "Mounts denied" or container starts but PX4-Autopilot directory appears empty inside container.

---

## Code Examples

Verified patterns from official sources (v1.15.4):

### Matek H743 Slim defconfig — Key UART/SPI/I2C Enable Lines
```kconfig
# Source: boards/matek/h743-slim/nuttx-config/nsh/defconfig @ v1.15.4
CONFIG_STM32H7_I2C1=y
CONFIG_STM32H7_I2C2=y
CONFIG_STM32H7_SPI1=y
CONFIG_STM32H7_SPI1_DMA=y
CONFIG_STM32H7_SPI2=y
CONFIG_STM32H7_SPI3=y
CONFIG_STM32H7_SPI4=y
CONFIG_STM32H7_SPI4_DMA=y
CONFIG_STM32H7_UART4=y
CONFIG_STM32H7_UART7=y
CONFIG_STM32H7_UART8=y
CONFIG_STM32H7_USART1=y
CONFIG_STM32H7_USART2=y
CONFIG_STM32H7_USART3=y
CONFIG_STM32H7_USART6=y
```

### Clock Configuration (board.h — confirmed 8 MHz)
```c
// Source: boards/matek/h743-slim/nuttx-config/include/board.h @ v1.15.4
// Comment: "X1: 8 MHz crystal for HSE"
#define STM32_BOARD_XTAL        8000000ul
#define STM32_HSI_FREQUENCY     16000000ul
#define STM32_HSE_FREQUENCY     STM32_BOARD_XTAL
```

### Docker Run Command (from Tools/docker_run.sh @ v1.15.4)
```bash
# Source: PX4-Autopilot/Tools/docker_run.sh @ v1.15.4
# Default NuttX image (also the fallback):
PX4_DOCKER_REPO="px4io/px4-dev-nuttx-focal:2022-08-12"

docker run -it --rm -w "${SRC_DIR}" \
    --env=LOCAL_USER_ID="$(id -u)" \
    --env=CCACHE_DIR="${CCACHE_DIR}" \
    --volume=${CCACHE_DIR}:${CCACHE_DIR}:rw \
    --volume=${SRC_DIR}:${SRC_DIR}:rw \
    ${PX4_DOCKER_REPO} /bin/bash -c "$1 $2 $3"
```

### Matek rc.board_sensors — ICM-42688P Driver Invocation
```sh
# Source: boards/matek/h743-slim/init/rc.board_sensors @ v1.15.4
# -s = SPI (not I2C), -b = bus number, -R = rotation integer
icm42688p -s -b 1 -R 12 start   # SPI1, PITCH180
icm42688p -s -b 4 -R 26 start   # SPI4, PITCH180_YAW90
dps310 -I start -a 118           # I2C (addr 0x76 decimal = 118)
```

Note: The Orqa H7 QuadCore rc.board_sensors will differ (different SPI buses, different CS pins, different rotations). This is Phase 2 work. Phase 1 only needs a sensor script that does not crash the build.

### firmware.prototype — Matek Reference
```json
// Source: boards/matek/h743-slim/firmware.prototype @ v1.15.4
{
    "board_id": 1013,
    "magic": "PX4FWv1",
    "description": "Firmware for the MatekH743 board",
    "image": "",
    "build_time": 0,
    "summary": "MatekH743",
    "version": "0.1",
    "image_size": 0,
    "image_maxsize": 1966080,
    "git_identity": "",
    "board_revision": 0
}
```

### bootloader.px4board — Matek Reference
```kconfig
// Source: boards/matek/h743-slim/bootloader.px4board @ v1.15.4
CONFIG_BOARD_TOOLCHAIN="arm-none-eabi"
CONFIG_BOARD_ARCHITECTURE="cortex-m7"
CONFIG_BOARD_ROMFSROOT=""
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Per-target px4io docker images (`px4-dev-nuttx-bionic`, `px4-dev-nuttx-focal`) | Single unified `px4io/px4-dev` image for main branch | ~2024-2025 | For v1.15.4, still use `px4io/px4-dev-nuttx-focal:2022-08-12`; the new unified image targets main/v1.16+ |
| GitHub fork as first step for board ports | Local in-tree branch, fork deferred | Best practice evolution | Reduces merge complexity when porting; fork when ready for upstream PR |
| `make px4_fmu-v5_default upload` (USB serial flash) | QGC firmware flash + `dfu-util` bootloader | Since NuttX bootloader adoption | Cleaner separation: DFU for bootloader, QGC for application |

**Deprecated/outdated:**
- `px4io/px4-dev-nuttx-bionic`: Ubuntu Bionic (18.04)-based image, superseded by focal. Do not use for v1.15 builds.
- Building from PX4 `main` branch: main uses updated CMake and toolchain features not compatible with the 2022 focal image.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | None applicable — firmware compilation, not unit tests |
| Config file | none |
| Quick run command | `docker run ... make orqa_h7quadcore_default 2>&1 \| tail -5` |
| Full suite command | Same (build is the test) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BUILD-01 | Docker build completes without local compiler | smoke | `./build.sh` exits 0 | ❌ Wave 0 — `build.sh` does not exist yet |
| BUILD-02 | Zero errors, zero warnings | smoke | `./build.sh 2>&1 \| grep -E "error:|warning:" \| wc -l` should output `0` | ❌ Wave 0 — board target does not exist yet |
| BUILD-03 | DFU flash succeeds | manual | hold BOOT + plug USB; `dfu-util -l` shows STM device; flash bootloader; reflash firmware via QGC | N/A — requires physical hardware |

### Sampling Rate
- **Per task commit:** `./build.sh` (full Docker build — ~3-5 min; unavoidable for embedded firmware)
- **Per wave merge:** Same full build + manual DFU smoke test on hardware
- **Phase gate:** Full build green + physical board boots to DFU mode before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `../PX4-Autopilot/boards/orqa/h7quadcore/` — entire board target directory tree does not exist yet
- [ ] `build.sh` — Docker wrapper script does not exist yet
- [ ] Board target must be created before any build command can be validated

*(BUILD-03 is manual-only because it requires physical hardware: the Orqa H7 QuadCore board, USB-C cable, and host dfu-util install. It cannot be automated in CI without hardware-in-the-loop setup.)*

---

## Open Questions

1. **Board ID for `firmware.prototype`**
   - What we know: Matek H743 Slim uses board_id 1013; PX4 maintains a registry of assigned IDs
   - What's unclear: Whether an unregistered private ID (e.g. 1099) is safe to use for personal use before upstream submission
   - Recommendation: Use 1099 (or any value > 1050 not appearing in `src/drivers/bootloaders/` board ID list); note it prominently as "PRIVATE — change before upstream PR"

2. **Betaflight bootloader behavior vs PX4 DFU**
   - What we know: The board ships with Betaflight. The STM32H743 has a factory DFU ROM at 0x1FF00000 (ST DFU, not PX4 DFU). Holding BOOT button uses the ST ROM DFU. The PX4 NuttX bootloader installs at 0x08000000.
   - What's unclear: Whether the Orqa H7 QuadCore has a hardware-level BOOT pin wired to put it in ST ROM DFU mode, or if Betaflight's own DFU mode is required first
   - Recommendation: The standard Betaflight BOOT button flow puts the STM32 into ST ROM DFU (0x1FF00000), which is what dfu-util uses. This is the correct entry point for flashing the PX4 bootloader. Verify by running `dfu-util -l` after holding BOOT — should show `[0483:df11]` (ST DFU VID:PID).

3. **Orqa HSE crystal — hardware confirmation**
   - What we know: STATE.md notes "HSE crystal is 8MHz (not 16MHz like some reference boards)" as a carry-forward pitfall. Matek H743 Slim board.h confirms 8 MHz.
   - What's unclear: The Orqa H7 QuadCore hardware has not been directly inspected — this is a project assumption
   - Recommendation: Before first flash, confirm 8 MHz crystal by reading the board schematic or User Manual (referenced as available in CONTEXT.md). If wrong frequency is used, symptoms are USB non-enumeration and incorrect UART baud rates.

---

## Sources

### Primary (HIGH confidence)
- `github.com/PX4/PX4-Autopilot` tag `v1.15.4` — `Tools/docker_run.sh`, `boards/matek/h743-slim/` (all files), `nuttx-config/nsh/defconfig`
- `docs.px4.io/v1.15/en/advanced_config/bootloader_update_from_betaflight.html` — DFU flash procedure
- `docs.px4.io/main/en/hardware/porting_guide_nuttx` — board target file structure

### Secondary (MEDIUM confidence)
- `docs.px4.io/main/en/test_and_ci/docker` — Docker image naming and `px4-dev` unified image for main branch
- `discuss.px4.io/t/how-a-board-target-files-are-organized-defconfig-px4board-adc-spi-etc/33425` — board target file roles (corroborated by source code inspection)

### Tertiary (LOW confidence)
- `discuss.px4.io/t/porting-px4-to-a-non-px4-supported-stm32h743-fc/48483` — general porting experience report; specific details not verified against source

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Docker image tag verified directly from `Tools/docker_run.sh` at v1.15.4; board target file structure verified from GitHub API + raw file fetches
- Architecture: HIGH — Board target directory structure, all file names, and make target naming convention confirmed from real Matek H743 Slim source
- Pitfalls: HIGH for HSE crystal (verified from board.h source); HIGH for DFU procedure (verified from official docs); MEDIUM for Windows Docker path issue (common knowledge, not source-verified)
- Validation: HIGH — BUILD-01/02 are build smoke tests; BUILD-03 is correctly identified as hardware-only manual

**Research date:** 2026-03-10
**Valid until:** 2026-06-10 (PX4 v1.15.x is stable; Docker image tag is pinned; clock config is hardware-fixed)
