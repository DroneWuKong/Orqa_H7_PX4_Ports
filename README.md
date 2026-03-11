# PX4 Port — Orqa H7 QuadCore

PX4 flight controller firmware port for the **Orqa H7 QuadCore** (STM32H743VIT6, 8 MHz HSE).

> **Status: Phase 1 Complete — Firmware compiles and boots. Sensors not yet configured.**

---

## Hardware

| Component | Details |
|-----------|---------|
| MCU | STM32H743VIT6 |
| HSE Crystal | 8 MHz |
| IMU 1 | ICM-42688-P on SPI1 (180° rotation) |
| IMU 2 | ICM-42688-P on SPI3 (90° CCW rotation) |
| Board ID | 1099 (temporary — must change before upstream PR) |

---

## What Works

- [x] Firmware compiles cleanly against PX4 v1.15.4
- [x] Bootloader compiles cleanly
- [x] Board target discoverable by PX4 build system
- [x] Docker build wrapper (`build.sh`)

## What Doesn't Work Yet

- [ ] IMU drivers not configured (GPIO pin assignments pending from Orqa)
- [ ] Sensors not started at boot
- [ ] No flight testing

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
git clone --branch v1.15.4 --recurse-submodules \
  https://github.com/PX4/PX4-Autopilot.git
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

### 3. Build firmware (Windows via WSL2)

Create a Docker build volume (first time only):

```bash
docker volume create px4-build

docker run --rm \
  --mount type=bind,source=$(pwd)/../PX4-Autopilot,target=/src-host \
  --mount type=volume,source=px4-build,target=/px4 \
  px4io/px4-dev-nuttx-focal:2022-08-12 \
  cp -a /src-host/. /px4/
```

Then build:

```bash
printf '#!/bin/sh\ngit config --global --add safe.directory /px4\nfind /px4 -name "*.sh" -exec sed -i s/\\r// {} +\nmake -C /px4 orqa_h7quadcore_default\n' > /tmp/px4build.sh

docker run --rm \
  --mount type=volume,source=px4-build,target=/px4 \
  --mount type=bind,source=/tmp/px4build.sh,target=/tmp/px4build.sh \
  px4io/px4-dev-nuttx-focal:2022-08-12 \
  sh /tmp/px4build.sh
```

### 3. Build firmware (Linux/macOS)

```bash
cd PX4-Autopilot
make orqa_h7quadcore_default
```

### 4. Build bootloader

Same as above but replace `orqa_h7quadcore_default` with `orqa_h7quadcore_bootloader`.

---

## Output Artifacts

| File | Description |
|------|-------------|
| `build/orqa_h7quadcore_default/orqa_h7quadcore_default.px4` | Main firmware (flash via QGroundControl) |
| `build/orqa_h7quadcore_default/orqa_h7quadcore_default.bin` | Raw binary |
| `build/orqa_h7quadcore_bootloader/orqa_h7quadcore_bootloader.bin` | Bootloader (flash via DFU) |

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
4. Choose `orqa_h7quadcore_default.px4`

---

## Known Issues / Limitations

- **Sensors not configured**: IMU GPIO pin assignments (SPI CS, EXTI interrupt pins) are pending hardware documentation from Orqa. See `ORQA_PIN_REQUEST.md` for the full list of what's needed.
- **board_id 1099**: Temporary private ID. Must be assigned a proper ID before any upstream PX4 PR.
- **Build only tested on Windows + WSL2 + Docker**: Linux/macOS builds should work but are untested.

---

## Testing Needed

If you have an Orqa H7 QuadCore board and can test, the most useful things right now are:

1. **DFU flash** — does the bootloader flash successfully and does the board enumerate over USB?
2. **QGroundControl connection** — does QGC see the board after firmware flash?
3. **GPIO pin assignments** — if you have access to the schematic or CubeMX file, see `ORQA_PIN_REQUEST.md`

Please open an issue or contact [@DroneWuKong](https://github.com/DroneWuKong) with results.

---

## Project Structure

```
boards/orqa/h7quadcore/     Board support package files (copy into PX4-Autopilot/boards/)
build.sh                    Docker build wrapper for Windows
ORQA_PIN_REQUEST.md         Pin information needed from Orqa for Phase 2
.planning/                  Project planning documents (GSD workflow)
```

---

## Roadmap

| Phase | Goal | Status |
|-------|------|--------|
| 1 — Scaffold and Build | Clean-compiling BSP + Docker build wrapper | ✅ Complete |
| 2 — Sensors and Console | IMU drivers, USB console, sensor validation | ⏳ Blocked (need GPIO pins) |
| 3 — Motor Outputs | PWM output mapping, ESC protocol | 📋 Planned |
| 4 — GPS and Magnetometer | GPS/mag driver bring-up | 📋 Planned |
| 5 — Flight Validation | Full flight test, parameter tuning | 📋 Planned |

---

## PX4 Version

Targeting **PX4 v1.15.4** with Docker image `px4io/px4-dev-nuttx-focal:2022-08-12`.
