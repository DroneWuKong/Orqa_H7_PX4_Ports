# Roadmap: PX4 Port — Orqa H7 QuadCore

**Project:** PX4 Port — Orqa H7 QuadCore (STM32H743)
**Core Value:** PX4 boots, dual IMU + baro are correctly mapped, and the quad flies stably in Stabilized mode
**Granularity:** Coarse
**Created:** 2026-03-10

---

## Phases

- [x] **Phase 1: Scaffold and Build** — Board target compiles cleanly from a reproducible toolchain (completed 2026-03-11)
- [ ] **Phase 2: Sensors and Console** — USB console works, all sensors detected and publishing, QGC connected
- [ ] **Phase 3: Motor Outputs** — All motors respond to DSHOT commands, bidirectional RPM telemetry confirmed
- [ ] **Phase 4: GPS and Magnetometer** — GPS fix acquired outdoors, magnetometer heading published
- [ ] **Phase 5: Flight Validation** — Sensor calibration complete, arming checks pass, stable Stabilized mode flight achieved

---

## Phase Details

### Phase 1: Scaffold and Build
**Goal**: Developer has a reproducible build environment and a clean-compiling board target ready to flash
**Depends on**: Nothing (first phase)
**Requirements**: BUILD-01, BUILD-02, BUILD-03
**Success Criteria** (what must be TRUE):
  1. Developer can run a single Docker command and produce a `.px4` firmware binary for `orqa/h7quadcore` without installing any local compiler
  2. The build completes with zero errors and zero warnings
  3. Developer can enter DFU mode and flash the firmware to the physical board using the boot button
**Plans**: 1 plan

Plans:
- [ ] 01-01-PLAN.md — Scaffold board target from Matek H743 Slim, write build.sh, flash via DFU

### Phase 2: Sensors and Console
**Goal**: Board is alive — USB console accessible, all sensor drivers detected and publishing data, QGroundControl connected over USB MAVLink
**Depends on**: Phase 1
**Requirements**: HW-01, HW-02, HW-03, HW-04, IMU-01, IMU-02, IMU-03, BARO-01, UART-01, UART-02, UART-03, UART-04, UART-05
**Success Criteria** (what must be TRUE):
  1. USB-C connection shows an `nsh>` prompt and the heartbeat LED is blinking
  2. `icm42688p status` reports both Gyro 1 (SPI1) and Gyro 2 (SPI4) as healthy, with WHO_AM_I=0x47 confirmed and uORB sensor topics publishing at expected rate
  3. Moving the board by hand produces correct-sign axis changes for both IMUs, confirming CW270 and CW180 rotation constants
  4. `dps310 status` shows plausible pressure and temperature values; QGC altitude estimate is stable
  5. UART3, UART6, UART7, UART8 are mapped and functional; QGroundControl connects via USB MAVLink and shows vehicle status including battery voltage
**Plans**: TBD

### Phase 3: Motor Outputs
**Goal**: All motor outputs deliver correct DSHOT300 signal; ESC3030 responds and echoes RPM telemetry
**Depends on**: Phase 2
**Requirements**: MOT-01, MOT-02
**Success Criteria** (what must be TRUE):
  1. `motor_test` spins all four (M1-M4) motors in the correct direction with props removed and no DMA conflicts with running sensor drivers
  2. A logic analyzer on each motor pin confirms valid DSHOT300 bit timing (prescaler=0, period=800 counts at 240MHz timer clock)
  3. Bidirectional DSHOT RPM telemetry from ESC3030 is visible as per-motor RPM values in QGroundControl
**Plans**: TBD

### Phase 4: GPS and Magnetometer
**Goal**: GPS module and magnetometer are detected, publishing navigation data, and capable of achieving a 3D fix outdoors
**Depends on**: Phase 2
**Requirements**: GPS-01, GPS-02, GPS-03
**Success Criteria** (what must be TRUE):
  1. GPS module on UART7 is detected and publishing position uORB topics visible in QGC
  2. Magnetometer on I2C1 is detected and publishing heading data in QGC
  3. Outdoor test achieves a 3D GPS fix with position accuracy sufficient for Position mode use
**Plans**: TBD

### Phase 5: Flight Validation
**Goal**: All sensor calibrations complete, arming checks pass, and the quad achieves stable controlled flight in Stabilized mode
**Depends on**: Phase 3, Phase 4
**Requirements**: FLY-01, FLY-02, FLY-03
**Success Criteria** (what must be TRUE):
  1. QGroundControl sensor calibration wizard completes without errors for accelerometer, gyroscope, magnetometer, and GPS
  2. Flight controller arms without errors and all four motors spin at idle throttle
  3. Pilot can fly the quad in Stabilized mode, confirming pitch/roll/yaw authority and stable hover
**Plans**: TBD

---

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Scaffold and Build | 1/1 | Complete   | 2026-03-11 |
| 2. Pin Map and Sensors | complete | ✅ Complete | 2026-03-16 |
| 3. Motor Outputs | 0/? | Not started | - |
| 4. GPS and Magnetometer | 0/? | Not started | - |
| 5. Flight Validation | 0/? | Not started | - |

---

## Coverage

| Requirement | Phase |
|-------------|-------|
| BUILD-01 | Phase 1 |
| BUILD-02 | Phase 1 |
| BUILD-03 | Phase 1 |
| HW-01 | Phase 2 |
| HW-02 | Phase 2 |
| HW-03 | Phase 2 |
| HW-04 | Phase 2 |
| IMU-01 | Phase 2 |
| IMU-02 | Phase 2 |
| IMU-03 | Phase 2 |
| BARO-01 | Phase 2 |
| UART-01 | Phase 2 |
| UART-02 | Phase 2 |
| UART-03 | Phase 2 |
| UART-04 | Phase 2 |
| UART-05 | Phase 2 |
| MOT-01 | Phase 3 |
| MOT-02 | Phase 3 |
| GPS-01 | Phase 4 |
| GPS-02 | Phase 4 |
| GPS-03 | Phase 4 |
| FLY-01 | Phase 5 |
| FLY-02 | Phase 5 |
| FLY-03 | Phase 5 |

**v1 requirements mapped: 24/24 ✓**

---
*Roadmap created: 2026-03-10*
*Phase 1 planned: 2026-03-10*
