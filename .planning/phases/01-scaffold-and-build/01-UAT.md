---
status: complete
phase: 01-scaffold-and-build
source: 01-01-SUMMARY.md
started: 2026-03-10T00:00:00Z
updated: 2026-03-11T00:00:00Z
---

## Current Test

number: 6
name: Bootloader builds successfully (requires Docker)
expected: |
  Running `./build.sh orqa_h7quadcore_bootloader` completes with exit 0 and produces ../PX4-Autopilot/build/orqa_h7quadcore_bootloader/orqa_h7quadcore_bootloader.bin
awaiting: user response

## Tests

### 1. Board target files exist in PX4-Autopilot
expected: The directory ../PX4-Autopilot/boards/orqa/h7quadcore/ exists and contains all required config files: firmware.prototype, default.px4board, bootloader.px4board, nuttx-config/, src/, init/
result: pass

### 2. Make targets are discoverable
expected: Running `find boards -maxdepth 3 -mindepth 3 -name '*.px4board' | grep orqa` from inside PX4-Autopilot returns two lines: boards/orqa/h7quadcore/bootloader.px4board and boards/orqa/h7quadcore/default.px4board
result: pass

### 3. HSE crystal value is correct
expected: Running `grep STM32_BOARD_XTAL boards/orqa/h7quadcore/nuttx-config/include/board.h` from inside PX4-Autopilot returns `#define STM32_BOARD_XTAL        8000000ul`
result: pass

### 4. build.sh exists and is executable
expected: `ls -la build.sh` in the project root shows the file exists with execute permissions (x flag set)
result: pass

### 5. build.sh produces firmware (requires Docker)
expected: Running `./build.sh` from project root (with Docker installed and running) completes with exit 0 and produces ../PX4-Autopilot/build/orqa_h7quadcore_default/orqa_h7quadcore_default.px4
result: pass

### 6. Bootloader builds successfully (requires Docker)
expected: Running `./build.sh orqa_h7quadcore_bootloader` completes with exit 0 and produces ../PX4-Autopilot/build/orqa_h7quadcore_bootloader/orqa_h7quadcore_bootloader.bin
result: pass

### 7. DFU flash to hardware (requires Docker + physical board)
expected: With Orqa H7 QuadCore connected via USB-C in DFU mode, running the DFU flash procedure from 01-01-PLAN.md Task 3 completes successfully and the board boots PX4
result: skipped
reason: Hardware not available yet

## Summary

total: 7
passed: 6
issues: 0
pending: 0
skipped: 1

## Gaps

[none yet]
