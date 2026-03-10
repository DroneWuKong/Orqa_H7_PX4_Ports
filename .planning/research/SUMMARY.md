# Project Research Summary

**Project:** PX4 Port — Orqa H7 QuadCore (STM32H743)
**Domain:** Embedded firmware — PX4 board target for FPV quadcopter flight controller
**Researched:** 2026-03-10
**Confidence:** MEDIUM (training data only; no live web access during any research session; verify key details against current PX4 main branch)

## Executive Summary

This project is a firmware board port — not application development. The deliverable is a new board target in the PX4-Autopilot tree (`boards/orqa/h7quadcore/`) that maps the Orqa H7 QuadCore's STM32H743 hardware to the PX4 flight stack via NuttX RTOS. The correct approach is copy-then-diff from the Matek H743 Slim (`boards/matek/h743-slim/`), which uses the same MCU, has a similar peripheral layout, and is already proven in the PX4 tree. The diff between Matek and Orqa is roughly 30 lines of pin assignments. The NuttX defconfig (~900 lines), CMake module list, and PX4 startup scripts are the three artifacts that define the entire port; getting these right is the whole job.

The v1 scope is deliberately narrow: boot to NuttX shell, USB MAVLink/QGC connection, both ICM-42688-P IMUs, DPS310 barometer, 8-channel unidirectional DSHOT motor output, UART3 RC receiver input, and ADC battery monitoring. This is enough to fly Stabilized mode and validate the port. Bidirectional DSHOT, W25Q128 flash blackbox, CAN bus, GPS, and upstream PR polish are all explicitly deferred. Scope discipline here is critical — every deferred feature is a potential DMA conflict or flash-budget problem that could block first flight.

The dominant technical risk on this project is STM32H743 DMA stream conflicts. The Orqa board runs SPI1 (Gyro1), SPI4 (Gyro2), SPI2 (flash, deferred), four DSHOT timers (TIM2/3/4/5, each needing a DMA stream), four UARTs, and I2C2 — all fighting for 8 streams per DMA controller. This must be mapped explicitly before writing any configuration, using the Betaflight DMA resource dump as a validated reference for this exact board. The second major risk is the HSE crystal frequency: the Orqa uses 8MHz where many reference boards use 16MHz; copying the Matek config without correcting this will produce a 240MHz (half-speed) system where everything appears to work but timing-sensitive peripherals (DSHOT, UART baud rates) are silently wrong.

## Key Findings

### Recommended Stack

PX4 firmware board targets use a fixed, prescribed toolchain. The build system is CMake/Ninja with a pinned `arm-none-eabi-gcc` from ARM Launchpad (do not use the system package manager's version — version mismatches cause subtle FPU/ABI bugs). NuttX RTOS is PX4's bundled fork at `platforms/nuttx/NuttX/`; do not use upstream NuttX independently. The Docker image `px4io/px4-dev-nuttx:latest` provides a hermetic build environment matching PX4 CI exactly and is the recommended environment for first builds and CI parity checks.

See `STACK.md` for full toolchain table, build commands, and directory structure.

**Core technologies:**
- arm-none-eabi-gcc (PX4-pinned, from `Tools/setup/ubuntu.sh`): cross-compiler — use the exact pinned version, not system apt
- CMake 3.22+ / Ninja 1.11+: build system — PX4 requires these versions; Ninja for fast incremental builds
- NuttX (PX4 bundled fork): RTOS — provides POSIX-like API; STM32H7 BSP is mature and covers all needed peripherals
- Docker `px4io/px4-dev-nuttx`: build environment — eliminates Python/tool version drift; matches CI exactly
- ST-LINK v2 + OpenOCD: debug and initial flash — mandatory for board bringup before USB bootloader works
- QGroundControl: validation — sensor calibration, MAVLink status, arming checks

**Critical version pins (verify against live PX4 main before building):**
- arm-none-eabi-gcc: 12.3.Rel1 (Launchpad) — check `Tools/setup/ubuntu.sh`
- CMake minimum: 3.22 — check repo root `CMakeLists.txt`
- NuttX bundled: 10.4.x (PX4 fork) — check `platforms/nuttx/NuttX/` submodule

### Expected Features

The feature set is divided into two scopes: v1 (first flight validation) and deferred (post-flight).

See `FEATURES.md` for full feature table, technical notes, and dependency graph.

**Must have (table stakes for v1 flight):**
- NuttX board config + `board_config.h` — without this, nothing boots
- ICM-42688-P dual IMU (SPI1 + SPI4) — at least one healthy gyro required to arm
- DPS310 barometer (I2C2, addr 0x77) — required for altitude estimation modes
- 8-channel DSHOT motor output (TIM2/3/4/5, unidirectional first) — most complex part of the port
- USB MAVLink / CDC-ACM console — primary interface for QGC during development
- UART3 RC receiver input — essential for manual flight
- ADC VBAT + current sense (PC0/PC1) — PX4 won't arm without battery reading
- SD card (SDMMC1) — logging; near-mandatory for flight debugging
- Actuator mixer config — generic quadrotor X (`SYS_AUTOSTART=4001`)

**Should have (post-first-flight differentiators):**
- Bidirectional DSHOT (RPM telemetry) — feeds PX4 dynamic notch filter; dramatically improves vibration rejection; defer until unidirectional validated
- W25Q128 SPI flash blackbox — 16MB flash for race setups without SD; medium complexity
- Beeper/buzzer (TIM1CH1, PE9) — arming tones; low complexity; improves UX
- Second ICM-42688 instance — reduces complexity during initial bringup; add after first flight
- Board-specific parameter defaults — upstream PR polish

**Defer to v2+:**
- CAN bus / UAVCAN / DroneCAN — adds 50+ KB flash, zero benefit for FPV acro
- GPS + magnetometer — requires weeks of EKF2 calibration; scope explosion
- MAX7456 OSD — irrelevant to PX4 stack
- Servo outputs (TIM15) — not needed for quad; declare pins but do not enable drivers

**Confirmed anti-features (do not build):**
- Dual-boot with Betaflight/iNav — PX4 overwrites everything; PX4-only from day one
- Advanced PX4 flight modes (Loiter, RTL, Auto) — require GPS+mag; fail confusingly without them

### Architecture Approach

A PX4 board target is a thin hardware description layer. It contains no flight logic — only hardware mapping. The layer stack is: PX4 Application Layer → PX4 Platform Layer → Board Target (`boards/orqa/h7quadcore/`) → NuttX RTOS → STM32H743 hardware. Sensor data flows from IMU hardware through SPI DMA, through PX4's icm42688p driver, into uORB topics consumed by EKF2 and rate controllers, which produce actuator outputs consumed by the DSHOT driver that fires DMA-backed timer pulses on the motor pins.

The recommended build order is: scaffold (copy + rename Matek) → boots to NSH → LEDs + ADC → Gyro1 → Gyro2 → Barometer → UARTs → motor outputs → SD + logging → integration + first flight. Each step has a clear deliverable and minimal debugging surface. Adding all drivers at once is the most common mistake; silent failures during `rc.board_sensors` make root cause ambiguous when multiple drivers are started simultaneously.

See `ARCHITECTURE.md` for full component detail, data flow diagrams, UART mapping table, DSHOT configuration patterns, and the complete 10-step build order.

**Major components:**
1. `CMakeLists.txt` — declares all PX4 driver modules and system modules included in the build; central manifest
2. `nuttx-config/h7quadcore/defconfig` — full NuttX kernel configuration; ~900 lines; controls clock, SPI/I2C/UART enables, DMA assignments
3. `nuttx-config/include/board.h` — hardware pin map for NuttX layer; clocks, UART AF remapping, DMA stream assignments
4. `src/board_config.h` — PX4-layer hardware constants; SPI chip selects, EXTI DRDY pins, sensor bus assignments
5. `init.d/rc.board_sensors` — NSH startup script; starts each sensor driver with explicit bus/CS/rotation args
6. `init.d/rc.board_defaults` — board-specific parameter defaults; DSHOT speed, ADC voltage scaling, motor ordering

### Critical Pitfalls

See `PITFALLS.md` for full detail on 15 pitfalls including phase-specific warning summary.

1. **Wrong HSE crystal frequency (8MHz vs 16MHz)** — The Matek H743 Slim may use 16MHz; the Orqa uses 8MHz. Copying without correction produces 240MHz (half-speed) CPU. DSHOT bit timing, UART baud rates, and USB enumeration all fail in non-obvious ways. Fix first: set `STM32_BOARD_XTAL=8000000` and verify PLL1 divisors before any peripheral work.

2. **DMA stream conflicts** — SPI1+SPI4 (both IMUs), TIM2/3/4/5 (8 DSHOT channels), UART DMA, and I2C2 all compete for 16 total DMA streams across two controllers. Conflicts cause silent peripheral failures — no error, just no data. Build a complete DMA allocation table from the STM32H743 RM0433 before writing any configuration. Use Betaflight's DMA resource dump for this exact board as the validated reference baseline.

3. **DSHOT DMA burst timing** — APB1 timer clock (TIM2/3/4/5) must be correctly computed from the PLL tree. At standard H743 config: AHB=240MHz, APB1=120MHz, timer input=240MHz (×2 multiplier applies). For DSHOT300: prescaler=0, period=800 counts. Wrong APB assignment produces bit timing off by 2x; ESCs don't arm but all other diagnostics look correct.

4. **Wrong IMU driver (ICM-42688-P vs ICM-42605)** — PX4 has separate drivers for these. ICM-42605 driver against ICM-42688 hardware will fail WHO_AM_I check (0x47 expected). Use `icm42688p` driver explicitly; do not rely on autodetection. Verify WHO_AM_I byte at SPI probe time before any calibration work.

5. **GPIO alternate function errors for motor pins** — STM32H743 GPIO pins have 16 AF options; wrong AF means the timer output never appears on the pin. DSHOT sends nothing and the symptom is identical to DMA misconfiguration. Cross-reference each motor pin against the STM32H743 datasheet (DS12110) AF table before writing board_config.h. Known correct AFs: PD12/PD13=TIM4 AF2, PA0/PA1=TIM2 AF1, PA2/PA3=TIM5 AF2, PB0/PB1=TIM3 AF2.

## Implications for Roadmap

Based on research, the natural structure follows the ARCHITECTURE.md build order, grouped into phases that each have a clear, verifiable deliverable. Each phase gates the next; there is no benefit to parallelizing across phases because failures at each step would produce ambiguous root causes.

### Phase 1: Environment and Scaffold

**Rationale:** Verify toolchain works against the reference board before touching any Orqa-specific files. Mistakes here are cheap; mistakes after 200 lines of board_config.h have been written are expensive.
**Delivers:** A successful `make matek_h743-slim_default` build proving the Docker/native toolchain is correctly configured; then a copy of the Matek target renamed to `boards/orqa/h7quadcore/` with all string references updated and `make orqa_h7quadcore_default` running CMake without errors (no flash required yet).
**Addresses:** All table-stakes features (they all depend on this scaffold existing)
**Avoids:** Pitfall 1 (HSE frequency) — this is the phase to set `STM32_BOARD_XTAL=8000000` and audit PLL divisors before flashing anything

### Phase 2: Hardware Bringup — Console and Power

**Rationale:** USB console must be proven before any sensor work begins. Without NSH, all subsequent driver failures produce no visible output and are nearly impossible to diagnose. LEDs and ADC are added here because they are the lowest-risk peripherals and provide visual confirmation of board state.
**Delivers:** `nsh>` prompt over USB, LED status indication, `adc test` showing battery voltage on PC0/PC1
**Addresses:** USB console (table stakes), ADC VBAT/CURR (table stakes), LED support (table stakes)
**Avoids:** Pitfall 10 (USB VBUS detect pin — PA9 must be set in board_config.h); Pitfall 11 (NSH console must be USB CDC-ACM, not UART3)
**Research flag:** Standard patterns — USB CDC-ACM on STM32H7 is well-documented; no deep research needed

### Phase 3: IMU Bringup (One at a Time)

**Rationale:** Start with the primary IMU only. Getting one ICM-42688-P working confirms SPI1 DMA, CS pin, DRDY interrupt, rotation constants, and the driver invocation syntax. Only after Gyro1 is confirmed publishing uORB topics does it make sense to add Gyro2 on SPI4.
**Delivers:** `icm42688p status` showing live sensor data for both instances; QGC sensor tab showing two IMUs; rotation verified against physical board
**Addresses:** Dual ICM-42688 registration (table stakes)
**Avoids:** Pitfall 4 (wrong driver variant — use `icm42688p`, WHO_AM_I=0x47); Pitfall 5 (SPI bus numbering — verify SPI4 maps to PX4 logical bus 4); Pitfall 13 (rotation enum off-by-one — CW270=14, CW180=8, verify in source); Pitfall 7 (init script ordering — check return codes after each start command)
**Research flag:** Needs live code validation — SPI bus logical numbering and `icm42688p start` flag syntax should be verified against the actual Matek H743 Slim source files before writing init scripts

### Phase 4: Barometer

**Rationale:** DPS310 on I2C2 is isolated from the SPI/DMA complexity of the IMU phase. It is a single peripheral with no DMA dependency, making it a low-risk confidence builder after IMU work. Baro is required for PX4 arming checks in many configurations.
**Delivers:** `dps310 status` showing pressure and temperature; altitude visible in QGC
**Addresses:** DPS310 barometer driver (table stakes)
**Avoids:** Pitfall 6 (DPS310 vs BMP280 confusion — probe with `i2cdetect 2` first, verify WHO_AM_I=0x10); confirm DPS310 not DPS368 (WHO_AM_I differs)
**Research flag:** Standard patterns — DPS310 driver is well-established in PX4; only gap is confirming exact Kconfig symbol name

### Phase 5: UART Assignments

**Rationale:** UARTs must be mapped before RC receiver or telemetry can be tested. This is also when the ttyS numbering is verified against the Matek reference (the ttySn order depends on defconfig enable sequence, not UART number). Validated with loopback test before connecting real hardware.
**Delivers:** UART3/6/7/8 enabled; ttyS assignments confirmed; MAVLink over UART6 connects to QGC via SiK telemetry
**Addresses:** UART assignments (table stakes), USB/MAVLink validation (table stakes)
**Avoids:** Pitfall 11 (console assignment conflicts — UART3 is VTx/RC, not NSH console)
**Research flag:** Standard patterns — UART configuration follows Matek reference exactly; main validation work is confirming ttyS numbers

### Phase 6: Motor Outputs (DSHOT)

**Rationale:** DSHOT is the most complex phase and is gated on the clock config being proven correct (Phase 2). All DMA stream assignments must be audited before this phase begins. Start with a logic analyzer on motor pins before connecting any ESCs.
**Delivers:** All 8 motors responding to `motor_test` with props removed; DSHOT300 confirmed with logic analyzer; no DMA conflicts with SPI or UART
**Addresses:** 8-channel DSHOT motor output (table stakes — most complex)
**Avoids:** Pitfall 2 (DMA stream conflicts — build full DMA map before writing defconfig; use Betaflight DMA resource dump as reference); Pitfall 3 (DSHOT timing — verify APB1=240MHz, prescaler=0, period=800 for DSHOT300); Pitfall 8 (GPIO AF errors — cross-reference STM32H743 datasheet for each motor pin AF); Pitfall 9 (8-channel output config — set `DIRECT_PWM_OUTPUT_CHANNELS=8`)
**Research flag:** Needs deeper research — DMA burst register offsets for TIM2/3/4/5 in PX4's `dshot.cpp` should be verified against current source before implementation. This is the highest-risk phase.

### Phase 7: Integration and First Flight

**Rationale:** All sensors confirmed, motors spinning. This phase configures the airframe, runs QGC sensor calibration, passes arming checks, and achieves stable Stabilized mode flight.
**Delivers:** Arming checks pass in QGC; Stabilized mode flight; SD card logging active; battery monitoring accurate
**Addresses:** Mixer/actuator output config (table stakes), SD card logging (table stakes), ADC scaling validation
**Avoids:** Pitfall 15 (ADC voltage scaling — BAT1_V_DIV from Betaflight 112/1/12 ratio must be converted to PX4 parameter); Pitfall 9 (airframe mixer — use `SYS_AUTOSTART=4001` for quad X)
**Research flag:** Standard patterns — QGC calibration workflow is well-documented

### Phase 8: Post-Flight Enhancements

**Rationale:** After first flight, scope expands to improve flight quality and completeness. Bidirectional DSHOT is the highest-value enhancement (feeds dynamic notch filter). W25Q128 flash and beeper are lower-risk additions.
**Delivers:** Bidir DSHOT with per-motor RPM telemetry; W25Q128 blackbox logging; beeper arming tones; second IMU (if deferred from Phase 3)
**Addresses:** Bidirectional DSHOT (differentiator), W25Q128 flash (differentiator), beeper (differentiator)
**Avoids:** Pitfall 12 (W25Q128 SPI2 DMA conflicts — verify SPI2 DMA stream doesn't conflict with now-proven TIM/SPI DMA map); Pitfall 14 (beeper TIM1_CH1 must not be in DSHOT timer list)

### Phase 9: Upstream PR

**Rationale:** The PR is submitted only after full hardware validation — PX4 maintainers require evidence of working hardware. This is the polish and documentation phase.
**Delivers:** Upstream PX4 PR with CI-passing build, flight test evidence, board documentation stub, maintainer listed in MAINTAINERS.md
**Avoids:** PR Pitfall 1 (missing docs), PR Pitfall 2 (non-standard CMake), PR Pitfall 3 (no hardware validation), PR Pitfall 4 (deprecated APIs)
**Research flag:** Needs review of current PX4 PR requirements — contribution guidelines may have evolved since training data cutoff

### Phase Ordering Rationale

- Phases 1-2 are environment and console: no hardware risk, cheap to redo, gate all future work
- Phase 3 (IMU) before Phase 4 (Baro) because IMU involves DMA and SPI complexity that must be resolved first; baro is DMA-free and isolated
- Phase 5 (UARTs) before Phase 6 (DSHOT) because UART ttyS mapping must be confirmed before any serial-dependent debugging of motor failures
- Phase 6 (DSHOT) is deliberately late: clock correctness from Phase 2 and DMA-free SPI from Phase 3 must be proven before adding 8 simultaneous DMA streams
- Phase 8 (enhancements) gated on first flight: bidir DSHOT and SPI2 flash introduce DMA changes that could destabilize the proven Phase 6 config
- Phase 9 (PR) is strictly last: submit only after hardware validation is complete

### Research Flags

Phases needing deeper research or live code validation during planning:
- **Phase 3 (IMU):** SPI bus logical numbering and exact `icm42688p start` flag syntax should be verified against actual `boards/matek/h743-slim/` source before writing init scripts — do not rely on training-data values for flag names
- **Phase 6 (DSHOT):** DMA burst register offsets and `DMAMAP_TIMx_UP` constants in `dshot.cpp` must be checked against current PX4 source — highest technical risk of the entire port
- **Phase 9 (PR):** Current PX4 upstream contribution requirements (MAINTAINERS.md format, doc PR process) should be verified against live PX4 contributor guide

Phases with standard, well-documented patterns (research-phase not needed):
- **Phase 1 (Scaffold):** Board directory structure and copy procedure are stable and well-documented
- **Phase 2 (Console):** USB CDC-ACM on STM32H7 follows standard PX4 patterns
- **Phase 4 (Baro):** DPS310 driver invocation is established; only gap is Kconfig symbol name verification
- **Phase 5 (UARTs):** UART configuration follows Matek reference; ttyS validation is a bench test, not research
- **Phase 7 (Integration):** QGC calibration and airframe selection are standard documented workflows

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Toolchain requirements are stable and verifiable; Docker image provides CI parity; only risk is pinned GCC version number which must be re-checked against live repo |
| Features | HIGH | v1 feature scope is clear and derives directly from PX4 arming requirements and project hardware; dependency graph is well-understood |
| Architecture | MEDIUM | Board target structure is stable and well-documented; specific file contents (ttyS numbering, DMA stream constants, driver flag syntax) must be verified against actual Matek H743 Slim source before writing code |
| Pitfalls | MEDIUM | Critical failure modes are well-identified from STM32H743 architecture knowledge; specific DMA stream assignments and DPS310 vs DPS368 variant require hardware-level validation |

**Overall confidence:** MEDIUM

### Gaps to Address

These items could not be resolved from training data and require validation against the actual PX4 repository or hardware before implementation:

- **Matek H743 Slim HSE frequency:** Confirm whether the Matek uses 8MHz or 16MHz HSE — this determines the exact PLL divisor diff needed. Check `boards/matek/h743-slim/nuttx-config/include/board.h` directly.
- **ttyS numbering order:** The mapping from UART3/6/7/8 to `/dev/ttySn` depends on the defconfig enable sequence. Values in ARCHITECTURE.md are approximate. Verify by reading Matek's serial console output or `stm32h7x3xx_serial.c` ordering.
- **icm42688p start flag syntax:** The `-R` rotation values (CW270=6 or 14? training data is inconsistent) must be verified against current `enum Rotation` in PX4 source. PITFALLS.md flags this as an off-by-one risk.
- **DPS310 vs DPS368 on Orqa board:** The two sensors have different WHO_AM_I values (0x10 vs 0x50). Confirm which is actually populated on the Orqa H7 QuadCore from the hardware manual or board markings.
- **W25Q128 PX4 driver name:** STACK.md rates this LOW confidence. The exact PX4 MTD driver for W25Q128FV must be identified from `src/drivers/` before Phase 8.
- **Bidir DSHOT support status:** STACK.md notes bidir DSHOT was added ~v1.14 but flags MEDIUM confidence on current status. Verify in current PX4 main before committing to Phase 8 scope.

## Sources

### Primary (HIGH confidence)
- PROJECT.md hardware specification — GPIO/SPI/I2C pin assignments, MCU, crystal frequency, Betaflight DMA resource dump reference
- PX4 Developer Guide: https://docs.px4.io/main/en/hardware/porting_guide.html — board porting procedure
- PX4 GitHub boards directory: https://github.com/PX4/PX4-Autopilot/tree/main/boards/ — reference board targets
- Matek H743-Slim reference: https://github.com/PX4/PX4-Autopilot/tree/main/boards/matek/h743-slim/ — primary copy-from reference
- STM32H743 Reference Manual RM0433 — DMA stream mapping, timer architecture, APB clock tree

### Secondary (MEDIUM confidence)
- Training-data knowledge of PX4 codebase (source structure stable since 2019; specific constant values and flag names may drift)
- PX4 upstream PR patterns from merged H743 board PRs circa 2022-2025 — contribution requirements
- Holybro KakuteH7: https://github.com/PX4/PX4-Autopilot/tree/main/boards/holybro/kakuteh7/ — DSHOT/FPV cross-reference

### Tertiary (LOW confidence — validate before use)
- W25Q128 PX4 driver mapping — training data inconclusive; check `src/drivers/mtd/` directly
- Bidirectional DSHOT current support status in PX4 main — verify against live codebase
- ICM-42688-P rotation enum integer values — verify against `src/lib/matrix/` in current PX4

---
*Research completed: 2026-03-10*
*Ready for roadmap: yes*
