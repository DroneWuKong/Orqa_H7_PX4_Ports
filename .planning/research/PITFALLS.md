# Domain Pitfalls

**Domain:** PX4 firmware port — STM32H743 FPV flight controller (Orqa H7 QuadCore)
**Researched:** 2026-03-10
**Confidence note:** External research tools unavailable during this session. All findings are from training-data domain knowledge cross-referenced against hardware specifics in PROJECT.md. Confidence levels reflect this. High-risk items should be validated against the Matek H743 Slim board source before implementation.

---

## Critical Pitfalls

Mistakes that cause rewrites, hardware damage, or PRs that are never merged.

---

### Pitfall 1: Wrong HSE Frequency in Clock Config

**What goes wrong:** The STM32H743 clock tree is configured in `stm32_rcc.c` and/or the board's `board_config.h`. The PLL multipliers assume a specific HSE input frequency. If you copy the Matek H743 Slim config and it uses a 16MHz crystal, but the Orqa board uses 8MHz (confirmed in PROJECT.md), the resulting CPU clock will be wrong — either half-speed (240MHz instead of 480MHz) or the board won't boot at all.

**Why it happens:** Developers diff-copy a reference board without checking the crystal. The Matek H743 Slim uses a 16MHz HSE. The Orqa H7 QuadCore uses 8MHz.

**Consequences:**
- At half-speed: board boots but all timing-sensitive peripherals (DSHOT, SPI, UART baud rates) will be off by 2x. DSHOT will fire at wrong bit times and ESCs won't respond. UARTs will have incorrect baud divisors. Symptoms look like random peripheral failures, not a clock issue.
- At wrong PLL: board hangs at reset, no USB, no NSH.

**Prevention:**
- In `boards/orqa/h7quadcore/nuttx-config/include/board.h`, set `STM32_BOARD_XTAL` to `8000000` (8MHz).
- Verify PLL1 settings: for 480MHz from 8MHz HSE, PLL1M=4 (÷4 = 2MHz ref), PLL1N=240 (×240 = 480MHz), PLL1P=1 (÷2? No — check that DIVM=4 gives 2MHz, then N=240 gives 480MHz VCO, P=1 for 480MHz core). Cross-check against STM32H743 datasheet maximum VCO range (192–836MHz).
- Compare your resulting `STM32_SYSCLK_FREQUENCY` against Matek H743 Slim to confirm both reach 480MHz despite different input crystals.

**Detection (warning signs):**
- DSHOT not working despite correct pin/timer assignment
- UART garbage output at expected baud rate settings
- USB enumeration failure
- `perf` command in NSH shows unrealistically fast or slow cycle counts

**Phase:** Clock bringup — first thing verified before any peripheral work.

---

### Pitfall 2: DMA Stream Conflicts on STM32H743

**What goes wrong:** The STM32H743 has two DMA controllers (DMA1, DMA2) and BDMA. Each stream can only service one request at a time. On a dense board like the Orqa H7 QuadCore (SPI1, SPI2, SPI3, SPI4, I2C2, 8x DSHOT timers, 4x UARTs, ADC), the default DMA stream assignments copied from the reference board may not match what's needed — or two peripherals may be assigned to the same stream.

**Why it happens:** STM32H743 DMA stream/channel mapping is defined in `stm32_dma.h` and board-level `board_config.h`. Copy-paste from Matek H743 Slim without auditing whether the Orqa board uses different peripherals on the same DMA streams.

**Specific conflicts to watch for this board:**
- SPI1 (Gyro 1) and SPI4 (Gyro 2) both need DMA. SPI1 maps to DMA1 or DMA2; SPI4 is typically DMA2. Confirm no overlap with DSHOT timer DMA.
- DSHOT on TIM2, TIM3, TIM4, TIM5 each need dedicated DMA streams. TIM2 → DMA1_STREAM7 (or similar). TIM3, TIM4, TIM5 each have defined DMA mappings in RM0433. All 4 timers × 2 channels = 8 DMA streams needed for 8-motor DSHOT. This is the most crowded resource on the chip.
- UART3 (DMA1 or DMA2 streams) may conflict with SPI DMA if naively assigned.
- SPI2 (W25Q128 flash) DMA can conflict with SPI1/SPI4 gyro DMA if they share a controller.

**Consequences:** Intermittent SPI read corruption on IMUs. DSHOT outputs drop randomly. Hard faults from DMA underrun/overrun. Symptoms are non-deterministic and very hard to debug without a logic analyzer.

**Prevention:**
- Build a complete DMA assignment table before writing any config. Map every peripheral that uses DMA to a specific DMAx_STREAMy_CHANNELz entry. Ensure no two peripherals share the same stream.
- Reference the STM32H743 Reference Manual (RM0433) Table "DMA1/DMA2 request mapping" as the ground truth.
- Check the Betaflight DMA config in `betaflight_4.4.1_STM32H743_ORQAH7QUADCORE.zip` — Betaflight has already solved this for this exact board. Extract the DMA assignments from the Betaflight resource dump and use them as your baseline.
- In PX4/NuttX, DMA assignments for DSHOT are in `dshot.cpp` and timer configs; for SPI they are in `stm32_spi.c`.

**Detection (warning signs):**
- IMU reads intermittently return stale/zero data
- DSHOT outputs work on some motors but not others
- NuttX hardfault at `DMA_IRQHandler` during boot
- `dmesg` / NSH shows DMA timeout or error messages

**Phase:** Critical to resolve before any peripheral driver work. Document the full DMA map in Phase 1 hardware bringup.

---

### Pitfall 3: DSHOT DMA Burst Mode vs. Per-Channel DMA

**What goes wrong:** PX4's DSHOT implementation on STM32H7 uses timer DMA burst transfers. The timer must be configured to use DMA burst on the correct register offset with the correct burst length. If the timer alternate function, channel, or burst register is wrong, DSHOT output is garbage even if the DMA streams are correctly assigned.

**Why it happens:** STM32H743 has timers on different APB buses (TIM2/TIM3/TIM5 on APB1, TIM1/TIM8/TIM15 on APB2). The clock prescaler applied to each APB differs. DSHOT bit timing depends on the actual timer input clock, not the CPU clock. Getting the prescaler wrong by a factor of 2 is easy (APB1 vs APB2 clock divide).

**Specific timing target for DSHOT300:**
- DSHOT300 = 300kbps → bit period = 3.33µs
- At 480MHz CPU with typical APB1 = 240MHz (÷2): TIM2/3/4/5 input clock = 240MHz (APB1 timers get ×2 multiplier if APB prescaler != 1)
- Actually with standard H743 clock tree: AHB = 240MHz, APB1 = 120MHz, TIM on APB1 = 240MHz (×2 multiplier)
- For DSHOT300 at 240MHz timer clock: prescaler=0 (÷1), period = 800 counts (240MHz / 300kHz = 800). T1H = ~600, T0H = ~300.

**Consequences:** ESCs don't arm (they receive garbled frames). Motors don't spin. Bidirectional DSHOT (telemetry) definitely fails.

**Prevention:**
- Check the Matek H743 Slim DSHOT configuration as the reference — same MCU, same clock tree, working implementation.
- In `dshot.cpp`/`dshot_mixer.cpp`, verify `DSHOT_DMA_BUFFER_SIZE` and timer burst configuration match your prescaler.
- Use a logic analyzer on one motor output to confirm bit timing before software debugging.
- Verify APB bus assignment for each timer: TIM2 is on APB1, TIM15 is on APB2. If you use TIM15 for servos, its clock rate differs from TIM2-5.

**Detection (warning signs):**
- ESC beacon/beep sequence plays but no arm response
- All 8 motors fail identically (suggests a timing issue, not a DMA conflict)
- Logic analyzer shows bit periods off by factor of 2

**Phase:** Phase after clock config is verified. Fix clock first, then DSHOT.

---

### Pitfall 4: ICM-42688-P vs ICM-42605 / ICM-42670 Driver Confusion

**What goes wrong:** PX4 has separate drivers for ICM-42686, ICM-42688, ICM-42605, and ICM-42670. These are NOT interchangeable. The ICM-42688-P is a high-performance gyro (32kHz ODR capable). ICM-42605 is a different die with different register map. ICM-42670 is a low-power variant with yet another interface.

**Why it happens:** The TDK InvenSense naming is confusing. Datasheets look similar. Developers see "ICM-426xx" and grab the wrong driver. In PX4, the driver is selected by `SENSORS_IMU_ICM42688P` (note: `ICM42688P` with P suffix). Using `ICM42605` driver against ICM-42688 hardware will fail WHO_AM_I check and the sensor won't initialize, or worse — on some silicon revisions, partial register compatibility may give a silent partial init that produces garbage data.

**Specific for this board:** Both IMUs are confirmed ICM-42688 (not 42605, not 42670). Use `ICM42688P` driver for both instances.

**ICM-42688-P WHO_AM_I register:** `0x47` (at register 0x75). ICM-42605 WHO_AM_I is `0x42`. If you see `0x42` returned when probing SPI1/SPI4, you have the wrong driver — or the wrong SPI config.

**Consequences:** Driver silently fails to attach (WHO_AM_I mismatch). No IMU data. PX4 arming checks fail. Quad won't arm.

**Prevention:**
- In `default.px4board`, use `CONFIG_DRIVERS_IMU_INVENSENSE_ICM42688P=y` for both IMUs.
- In the init script or sensor autodetect, explicitly probe `icm42688p start -s -b 1 -R 14` (SPI bus 1, rotation 14 = CW270) and `icm42688p start -s -b 4 -R 8` (SPI bus 4, rotation 8 = CW180). Don't rely on autodetection finding the wrong driver.
- Double-check rotations: PROJECT.md states Gyro1=CW270 (rotation 14 in PX4), Gyro2=CW180 (rotation 8 in PX4). Verify against PX4 rotation enum — off-by-one is easy here.

**Detection (warning signs):**
- `icm42688p status` shows no devices
- Boot log shows "WHO_AM_I mismatch" or probe failure on SPI bus 1 or 4
- `sensors` command shows 0 gyros/accels detected
- Trying `icm42605 start` instead accidentally shows success (wrong driver)

**Phase:** IMU driver work. Verify WHO_AM_I byte before any calibration work.

---

### Pitfall 5: Dual IMU SPI Configuration — Bus Numbers vs Physical SPI Peripherals

**What goes wrong:** PX4/NuttX SPI bus numbering does not always match STM32 SPI peripheral numbering. In NuttX for STM32H7, SPI1 is typically PX4 "SPI bus 1" and SPI4 is PX4 "SPI bus 4" — but this must be confirmed in the board's `board_config.h`. If SPI4 is mapped to a different logical bus number in the NuttX configuration, the driver `-b 4` argument will probe the wrong bus.

**Why it happens:** Some boards remap SPI peripherals to non-obvious bus numbers to avoid conflicts. The Matek H743 Slim may use different SPI bus numbering than you expect.

**Specific concern:** The Orqa board uses SPI1 (CS=PA4) for Gyro1 and SPI4 (CS=PE11) for Gyro2. If Betaflight shows these as "SPI1" and "SPI4", PX4's bus numbers should match if the board config is straightforward — but verify the `stm32_spibus_initialize()` calls in `board_config.h`.

**Consequences:** Second IMU never initializes. PX4 runs on single IMU silently — no error, just no redundancy. Or worse: driver is started on wrong bus, corrupts unrelated SPI peripheral (e.g., probing SPI2 flash with IMU init sequence).

**Prevention:**
- In `board_config.h`, confirm `#define PX4_SPI_BUS_SENSORS` and `#define PX4_SPI_BUS_SENSORS2` map to STM32 SPI1 and SPI4.
- In the startup script, verify both `icm42688p start` commands return success before proceeding.
- Use `spi status` in NSH to enumerate all SPI buses and their CS lines.

**Detection (warning signs):**
- `sensors` shows only 1 gyro
- `dmesg` shows second `icm42688p start` command returns error silently
- `uorb top` shows only one IMU topic publishing

**Phase:** IMU bring-up (Phase 2 hardware work).

---

### Pitfall 6: DPS310 vs BMP280 — Wrong Baro Driver

**What goes wrong:** PX4 has `dps310` and `bmp280` as separate drivers. Selecting `bmp280` for a DPS310 will silently fail (WHO_AM_I check: DPS310 returns `0x10` at register 0x0D; BMP280 returns `0x60` at register 0xD0). More subtle: DPS310 is an I2C baro at address 0x77 — which is the same I2C address as BMP280 default. A probe that doesn't check WHO_AM_I carefully might partially initialize and produce garbage altitude data.

**Why it happens:** Both sensors use the same I2C address (0x77). Both appear at the same location on the bus. The distinction is only in the WHO_AM_I register and register map.

**Specific for this board:** DPS310 on I2C2 at 0x77. Use `dps310 start -X -b 2` (external I2C bus 2, address 0x77). Do not use `bmp310` (that's a different sensor family entirely) or `bmp280`.

**DPS310 vs DPS368:** These are different sensors too. DPS310 WHO_AM_I = 0x10. DPS368 WHO_AM_I = 0x50. Confirm the Orqa board actually uses DPS310 and not DPS368 (the manual should clarify — both look identical externally and share the same package).

**Consequences:** Barometer reports garbage altitude. EKF altitude estimate is bad. Altitude hold / position modes won't work. For FPV acro-only v1 this is lower severity, but altitude data in QGC will look wrong and confuse troubleshooting.

**Prevention:**
- In `default.px4board`, use `CONFIG_DRIVERS_BARO_IFX007T_DPS310=y` (or the correct Kconfig symbol — verify exact name in PX4 source).
- In init script: `dps310 start -X -b 2` and check return code.
- Probe manually in NSH: `i2cdetect 2` should show device at 0x77. Then `i2c read 2 0x77 0x0D 1` should return 0x10 for DPS310.

**Detection (warning signs):**
- Baro driver start fails with "no device found"
- Altitude reading jumps to large/small nonsense values at boot
- `sensors` shows barometer not detected

**Phase:** Peripheral bringup. Verify with i2cdetect before driver work.

---

### Pitfall 7: NuttX NSH Init Script — Startup Order and Error Swallowing

**What goes wrong:** PX4's NSH init script (`init.d/rcS` or board-specific `extras.txt`) runs commands sequentially at boot. Two common errors:

1. **Starting IMU driver before SPI bus is initialized:** If the SPI bus enable / CS setup hasn't run yet, the IMU probe returns no device and PX4 silently continues. No retry logic exists. The IMU is simply absent for the rest of the session.

2. **Missing `set +e` / error-handling:** Some init commands are expected to fail gracefully (e.g., probing optional hardware). If the script treats all failures as fatal, board hangs on first missing device. If it ignores all failures, real failures are hidden.

**Why it happens:** Init scripts in PX4 are shell-like but limited. Error handling semantics differ from bash. Developers copying from reference boards may not understand which commands are guard-checked vs. fire-and-forget.

**Specific for this board:** The dual ICM-42688 init needs both `icm42688p start` calls to succeed. If only one succeeds, PX4 will run but with asymmetric IMU config — the rotation/calibration will be wrong for the "found" IMU depending on which one initialized.

**Consequences:** Silent single-IMU operation with wrong rotation applied. Unexpected flight dynamics. Hard to diagnose without `dmesg` review.

**Prevention:**
- After each sensor `start` command, check the return value explicitly: `if [ $? -ne 0 ]; then echo "SENSOR_NAME start FAILED"; fi`
- Follow the Matek H743 Slim init script structure exactly for ordering.
- Boot sequence order: 1) SPI buses init (happens in NuttX BSP before scripts), 2) IMU drivers, 3) Baro driver, 4) Other peripherals, 5) Mixer/airframe load, 6) PX4 modules start.

**Detection (warning signs):**
- `sensors` shows fewer devices than expected but no error messages
- Board appears to boot normally but QGC shows only partial sensor suite
- `dmesg | grep -i fail` reveals hidden failures

**Phase:** Init script work — treat as its own phase, not an afterthought.

---

### Pitfall 8: Motor Timer Alternate Function Mapping Errors

**What goes wrong:** STM32H743 GPIO pins have multiple alternate functions (AF0-AF15). Motor pin PD12 might be TIM4_CH1 at AF2, but if the `board_config.h` specifies AF1 instead, the timer output never appears on the pin (it outputs on some other function or is disconnected). DSHOT then sends nothing. The pin is in the right mode, the timer fires, but nothing reaches the ESC.

**Why it happens:** STM32H743 alternate function tables are in the datasheet Table "Alternate function" (typically 10+ pages). Copy-paste errors from Betaflight resource assignments (which don't specify AF numbers) to NuttX GPIO config macros (which do) are common.

**Specific motor pins and their AFs (from PROJECT.md, verify against datasheet):**
- PD12 → TIM4_CH1: AF2
- PD13 → TIM4_CH2: AF2
- PA1 → TIM2_CH2: AF1
- PA0 → TIM2_CH1: AF1
- PA2 → TIM5_CH3: AF2
- PA3 → TIM5_CH4: AF2
- PB1 → TIM3_CH4: AF2
- PB0 → TIM3_CH3: AF2

**Consequences:** DSHOT sends nothing. ESC sees no signal. Motor doesn't spin. Symptom identical to DMA misconfiguration or timer misconfiguration, making root cause diagnosis difficult.

**Prevention:**
- For each motor pin, look up the alternate function in the STM32H743 datasheet (DS12110) Table 11/12 "Alternate function mapping."
- In the PX4 board's `board_config.h`, the GPIO macro for each motor output must include the correct AF: e.g., `GPIO_TIM4_CH1OUT` which expands to include AF2.
- Cross-check: Betaflight's timer resource assignment shows *which* timer channel uses which pin, but not the AF. The datasheet is the only ground truth for AF numbers.

**Detection (warning signs):**
- Logic analyzer shows no signal on motor output pins despite timer running
- DMA completes without error but no output
- Some motors work, others don't (suggests per-pin AF error, not global timer issue)

**Phase:** Initial motor output verification. Use logic analyzer before connecting ESCs.

---

## Moderate Pitfalls

### Pitfall 9: Airframe/Mixer Selection for 8-Motor Output

**What goes wrong:** PX4 default airframe for a quadrotor uses only 4 motor outputs. For an 8-output board, the mixer must be configured to expose all 8 channels even if only 4 are used (for the quad). Using a wrong airframe will leave motors 5-8 uninitialized, which may leave those output pins in indeterminate states.

**Prevention:**
- Use a generic "Quadrotor X" airframe for v1 (4 motors). Verify `MIXER_FILE` in airframe config is `quad_x.main.mix` or equivalent.
- For 8-motor DSHOT output capability, ensure the PWM/DSHOT output module is configured for 8 channels total in `board_config.h` (`#define DIRECT_PWM_OUTPUT_CHANNELS 8`).
- Confirm unused outputs are configured as outputs and driven to disarmed value, not floating.

**Phase:** Airframe/mixer work after motor outputs verified.

---

### Pitfall 10: USB Detection Pin Configuration

**What goes wrong:** The Orqa board uses PA9 for USB VBUS detect. If this pin is not correctly configured as the USB VBUS sense input in `board_config.h`, USB may not enumerate at all, or may enumerate but immediately disconnect when VBUS is present (because the driver doesn't know USB is connected).

**Prevention:**
- In `board_config.h`, set `#define GPIO_OTGFS_VBUS` to PA9 with appropriate pull-down and input mode.
- Matek H743 Slim may use a different VBUS detect pin — do not copy blindly.

**Phase:** USB console bringup (early Phase 1).

---

### Pitfall 11: UART Assignment Conflicts with NSH Console

**What goes wrong:** PX4 on STM32H743 typically uses USART3 or UART7 for NSH debug console. If the board config assigns a different UART as the console but the `extras.txt` or `rcS` script tries to use yet another UART for MAVLink or telemetry, the wrong data appears on the wrong connector.

**Specific concern:** UART3 (PD8/PD9) is labeled "VTx/receiver connector" on the Orqa board. If NSH console is accidentally routed to UART3, NSH output goes to the VTX connector, not USB. USB serial becomes non-functional for development.

**Prevention:**
- USB console (USB CDC ACM) should be the primary NSH console for development — confirm `CONFIG_CDCACM_CONSOLE=y` in NuttX config.
- Do not assign UART3, UART6, UART7, UART8 as NSH console — reserve them for MAVLink/telemetry/RC.

**Phase:** Initial boot/console bringup.

---

### Pitfall 12: SPI Flash (W25Q128) Conflicting with SPI2 Bus

**What goes wrong:** SPI2 is used for the W25Q128 blackbox flash (CS=PB12). PX4 uses ROMFS/QSPI for some H7 boards, but W25Q128 on SPI2 needs the `w25qxxxjv` driver. If PX4 tries to use SPI2 for a different purpose (or if the SPI2 DMA clashes with another peripheral), the flash driver will fail silently and blackbox logging won't work.

**Prevention:**
- The flash is out-of-scope for v1 (FPV acro, no GPS logging needed immediately). Consider disabling the SPI2 flash driver entirely in v1 to reduce DMA pressure. Re-enable in a later phase.
- If enabled, ensure SPI2 CS (PB12) is correctly defined and its DMA stream doesn't conflict with SPI1/SPI4 gyro DMA.

**Phase:** Later phase after core functionality validated.

---

## Minor Pitfalls

### Pitfall 13: Rotation Constants Off by One

**What goes wrong:** PX4 sensor rotation enum values may shift between major PX4 versions. `ROTATION_YAW_270` (for Gyro1 CW270) must be verified against the current enum in `rotation.h`, not assumed from documentation.

**Prevention:**
- Look up `enum Rotation` in `src/lib/matrix/matrix/helper_functions.hpp` or `src/lib/ecl/geo/geo.h` for the exact integer values. CW270 = yaw 270 degrees. In PX4, `ROTATION_YAW_270 = 14`. CW180 = `ROTATION_YAW_180 = 8`. Verify these are still correct in the PX4 version you're building from.

**Phase:** IMU driver initialization.

---

### Pitfall 14: Beeper Pin Conflicts with Timer Capture

**What goes wrong:** The beeper is on PE9, TIM1_CH1. TIM1 is also potentially used for other outputs (it's the advanced-control timer). If TIM1_CH1 is configured for DSHOT or as a servo output, the beeper function is lost or worse — both try to drive PE9 simultaneously.

**Prevention:**
- The Orqa board assigns TIM1_CH1 exclusively to the beeper. TIM1 should not be in the DSHOT output timer list. Verify no motor or servo is assigned to TIM1_CH1.
- For servos, PROJECT.md shows TIM15 (PE5/PE6) — which is correct and separate from TIM1.

**Phase:** GPIO/timer assignment review.

---

### Pitfall 15: ADC Pin Voltage Scaling

**What goes wrong:** PX4's VBAT monitoring uses ADC with a scaling factor defined in `board_config.h`. The Orqa board uses 112/1/12 ratio for voltage and 108 for current (from Betaflight config). If the wrong ADC scaling is configured, QGC will show incorrect battery voltage, potentially causing early low-battery warnings or missed critical-voltage events.

**Prevention:**
- Set `BOARD_ADC_VOLTAGE_DIVIDER_SCALE` correctly from the Betaflight values. The 112/1/12 ratio means input divider gives VIN × (1/12) approximately. Verify VBAT pin (PC0) and CURR pin (PC1) are assigned to the correct ADC channels in `board_config.h`.

**Phase:** ADC/power monitoring work.

---

## PX4 Upstream PR Pitfalls

These cause PR rejections, not hardware failures.

### PR Pitfall 1: Incomplete or Missing Documentation

**What goes wrong:** PX4 requires a documentation PR alongside the board PR (in the PX4 user docs repo). Missing or stub documentation causes immediate rejection.

**Required docs:**
- Wiring diagram or pinout table
- Feature list (ports, protocols, constraints)
- Buy/product link
- Known issues

**Phase:** Upstream contribution phase.

---

### PR Pitfall 2: Hardcoded Absolute Paths or Non-Standard CMake

**What goes wrong:** Board `CMakeLists.txt` must use PX4 standard CMake macros (`px4_add_board`, `px4_add_common_flags`, etc.). Custom non-standard CMake will fail CI and be rejected in review.

**Prevention:**
- Copy the CMakeLists.txt structure from Matek H743 Slim exactly, only changing board-specific values.
- Run `make orqa_h7quadcore_default` in CI (GitHub Actions) before submitting PR to verify the build passes.

**Phase:** Upstream contribution phase.

---

### PR Pitfall 3: Un-Validated Hardware in PR

**What goes wrong:** PX4 maintainers require evidence of working hardware for new board PRs. A PR with a board target that has never booted on real hardware will be marked "needs testing." In practice, PRs without confirmed flight test data sit for months.

**Prevention:**
- Submit PR only after: boots to NSH, sensors detected, motors spin, QGC connects.
- Include a short video or log file showing QGC with sensor data as PR comment.

**Phase:** Upstream contribution is the final milestone, not concurrent with development.

---

### PR Pitfall 4: Using Deprecated PX4 APIs or Removed Features

**What goes wrong:** PX4 has been evolving rapidly. Features like `mixer` files (legacy), non-uORB sensor drivers, and old `px4_simple_app` patterns are removed or deprecated. Board targets using deprecated patterns will fail CI or get "needs rewrite" review comments.

**Prevention:**
- Use the current Matek H743 Slim as the reference — it is maintained in the active PX4 tree. If it uses a pattern, that pattern is current.
- Avoid referencing PX4 v1.12 or earlier documentation. Target the current main branch patterns.

**Phase:** Applies throughout all phases — use current reference board as the baseline.

---

## Phase-Specific Warning Summary

| Phase Topic | Likely Pitfall | Mitigation |
|-------------|---------------|------------|
| Clock/PLL config | Wrong HSE (8MHz vs 16MHz) producing 240MHz instead of 480MHz | Set `STM32_BOARD_XTAL=8000000`, verify PLL1N/M/P divisors |
| DMA assignment | SPI1+SPI4+TIM2/3/4/5 DSHOT DMA streams conflicting | Build full DMA map before any code; use Betaflight DMA assignments as reference |
| DSHOT timing | APB1 clock tree wrong, bit period off by 2x | Verify APB1 = 240MHz after PLL, compute prescaler/period for DSHOT300 |
| IMU driver selection | ICM-42605 driver used instead of ICM-42688-P | Explicitly use `icm42688p` driver, check WHO_AM_I = 0x47 |
| Dual IMU SPI buses | SPI4 mapped to wrong PX4 logical bus number | Audit `board_config.h` SPI bus mapping vs NuttX SPI init |
| Baro driver | DPS310 confused with BMP280 or DPS368 | Use `dps310` driver, probe with i2cdetect, check WHO_AM_I = 0x10 |
| NSH init script | Silent sensor init failures, wrong startup order | Check return codes after each `start` command |
| GPIO alternate functions | Timer AF wrong for motor pins, no output on pin | Cross-reference STM32H743 datasheet AF table for each motor pin |
| USB console | VBUS detect pin not configured | Set `GPIO_OTGFS_VBUS` to PA9 in `board_config.h` |
| Upstream PR | No docs, no confirmed flight test, deprecated APIs | Submit PR only after full hardware validation |

---

## Sources

- PROJECT.md hardware specification (confirmed GPIO/SPI/I2C assignments) — HIGH confidence
- PX4 source code architecture knowledge (training data, cross-referenced with known Matek H743 Slim port structure) — MEDIUM confidence
- STM32H743 DMA and timer architecture (RM0433 reference manual knowledge) — MEDIUM confidence
- PX4 PR review patterns and upstream contribution requirements (training data) — MEDIUM confidence
- ICM-42688-P WHO_AM_I and register specifics (InvenSense datasheet knowledge) — MEDIUM confidence
- DPS310 WHO_AM_I specifics — MEDIUM confidence (validate against Infineon DPS310 datasheet before implementation)

**Gaps requiring validation before implementation:**
- Exact PX4 logical bus numbers for SPI1 and SPI4 on STM32H743 boards (check Matek H743 Slim `board_config.h` directly)
- Current PX4 Kconfig symbol names for `dps310` and `icm42688p` drivers (check `src/drivers/` Kconfig files)
- Whether DPS310 or DPS368 is actually populated on the Orqa H7 QuadCore (check Orqa manual or board markings)
- DSHOT DMA burst register offsets for TIM2/3/4/5 on STM32H7 (check PX4 `dshot.cpp` implementation)
