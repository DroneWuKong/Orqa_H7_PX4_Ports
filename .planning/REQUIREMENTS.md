# Requirements: PX4 Port — Orqa H7 QuadCore

**Defined:** 2026-03-10
**Core Value:** PX4 boots, dual IMU + baro are correctly mapped, and the quad flies stably in Stabilized mode

## v1 Requirements

### Build System

- [ ] **BUILD-01**: Developer can build PX4 firmware for `orqa/h7quadcore` target using Docker/pinned toolchain (no local compiler setup required)
- [ ] **BUILD-02**: Board target compiles with zero errors and zero warnings
- [ ] **BUILD-03**: Developer can flash firmware to the board via DFU mode using the boot button

### Hardware Bringup

- [ ] **HW-01**: USB-C connection gives access to NSH console (`nsh>` prompt)
- [ ] **HW-02**: LED indicators respond to firmware (at minimum, heartbeat LED)
- [ ] **HW-03**: ADC battery voltage reads correctly (divider ratio 10/1.2, vbat scale 112)
- [ ] **HW-04**: ADC current sensor reads a value (scale 108, from ESC connector CURR pin)

### IMU

- [ ] **IMU-01**: ICM-42688-P Gyro 1 detected (SPI1, CS=PA4), WHO_AM_I=0x47 confirmed, publishing sensor data at expected rate
- [ ] **IMU-02**: ICM-42688-P Gyro 2 detected (SPI4, CS=PE11), WHO_AM_I=0x47 confirmed, publishing sensor data at expected rate
- [ ] **IMU-03**: Gyro rotations correctly set (Gyro1=CW270, Gyro2=CW180) — verified by moving board and checking sign of axes

### Barometer

- [ ] **BARO-01**: DPS310 detected (I2C2, addr 0x77), pressure and temperature readings plausible, altitude estimate stable

### UARTs

- [ ] **UART-01**: UART3 (PD8/PD9) functional — mapped for receiver (VTx connector)
- [ ] **UART-02**: UART6 (PC6/PC7) functional — mapped for SIK telemetry
- [ ] **UART-03**: UART7 (PE8/PE7) functional — mapped for GPS connector
- [ ] **UART-04**: UART8 (PE1/PE0) functional — mapped for ESC telemetry input
- [ ] **UART-05**: QGroundControl connects via USB MAVLink and shows vehicle status

### Motor Outputs

- [ ] **MOT-01**: M1–M4 DSHOT output functional — motors spin correctly when commanded
- [ ] **MOT-02**: Bidirectional DSHOT functional — RPM telemetry echoed back from ESC3030 and visible in QGC

### GPS & Magnetometer

- [ ] **GPS-01**: GPS module detected on UART7 (PE8/PE7) and publishing position data
- [ ] **GPS-02**: Magnetometer detected on I2C1 (SCL=PB6, SDA=PB7) and publishing heading data
- [ ] **GPS-03**: 3D GPS fix achieved outdoors with position hold accuracy sufficient for Position mode

### Flight Validation

- [ ] **FLY-01**: All sensor calibrations complete in QGroundControl (accel, gyro, magnetometer, GPS)
- [ ] **FLY-02**: FC arms without errors, all 4 motors spin at idle
- [ ] **FLY-03**: Quad achieves stable hover in Stabilized mode — pilot confirms controllability

## v2 Requirements

### Motor Outputs

- **MOT-V2-01**: M5–M8 DSHOT outputs functional (MFC connector — PA2, PA3, PB1, PB0)

### Blackbox

- **BLK-V2-01**: W25Q128FV SPI flash (SPI2, CS=PB12) usable for PX4 blackbox logging

### Navigation

- **NAV-V2-01**: Position Hold / Loiter mode validated in flight

### ISR / Dual Camera

- **ISR-V2-01**: PX4 can switch between two analog camera inputs (thermal + RGB) via GPIO (pin PB09 camera switch, already wired on board)
- **ISR-V2-02**: Camera switch controllable from MAVLink command or RC channel (no Betaflight pinio dependency)
- **ISR-V2-03**: Analog video OSD overlay (MAX7456, SPI3) functional under PX4 — shows flight telemetry on video feed
- **ISR-V2-04**: Payload trigger output functional via GPIO5 (PD14) — enables shutter/sensor trigger for ISR payloads

### Upstream

- **UPS-V2-01**: Board target submitted as PR to PX4 mainline repository
- **UPS-V2-02**: PR includes flight test evidence (logs or video)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Betaflight / iNav configuration | Already works, not this project |
| MAX7456 OSD | Analog OSD not used by PX4 stack |
| Camera switching (GPIO/PINIO) | Analog video feature, irrelevant to PX4 |
| Orqa Ghost/GHST receiver protocol | Configure in QGC after port is working |
| Position Hold / Loiter mode | GPS hardware bring-up is v1; assisted flight modes deferred to v2 |
| Upstream PX4 PR (v1) | Personal use first; upstream deferred to v2 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| BUILD-01 | Phase 1 | Pending |
| BUILD-02 | Phase 1 | Pending |
| BUILD-03 | Phase 1 | Pending |
| HW-01 | Phase 2 | Pending |
| HW-02 | Phase 2 | Pending |
| HW-03 | Phase 2 | Pending |
| HW-04 | Phase 2 | Pending |
| IMU-01 | Phase 2 | Pending |
| IMU-02 | Phase 2 | Pending |
| IMU-03 | Phase 2 | Pending |
| BARO-01 | Phase 2 | Pending |
| UART-01 | Phase 2 | Pending |
| UART-02 | Phase 2 | Pending |
| UART-03 | Phase 2 | Pending |
| UART-04 | Phase 2 | Pending |
| UART-05 | Phase 2 | Pending |
| MOT-01 | Phase 3 | Pending |
| MOT-02 | Phase 3 | Pending |
| GPS-01 | Phase 4 | Pending |
| GPS-02 | Phase 4 | Pending |
| GPS-03 | Phase 4 | Pending |
| FLY-01 | Phase 5 | Pending |
| FLY-02 | Phase 5 | Pending |
| FLY-03 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-10*
*Last updated: 2026-03-10 after roadmap creation (5-phase coarse mapping)*
