---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: In progress
last_updated: "2026-03-16T00:00:00.000Z"
progress:
  total_phases: 5
  completed_phases: 2
  total_plans: 1
  completed_plans: 1
  percent: 40
---

# Project State: PX4 Port — Orqa H7 QuadCore + Wingcore

**Last updated:** 2026-03-16
**Session:** Phase 2 complete — full pin map, sensor config, wingcore variant, ORQA official fork alignment

---

## Current Position

**Phase:** 2 — Pin Map and Sensors ✅ COMPLETE
**Next:** Phase 3 — Hardware Validation (requires physical board)

```
Progress: [████████░░░░░░░░░░░░] 40%
Phase 1 [█████] Phase 2 [█████] Phase 3 [     ] Phase 4 [     ] Phase 5 [     ]
```

---

## Completed Work

### Phase 1 — Scaffold and Build ✅
- Board target compiles against PX4
- Bootloader compiles
- Docker build wrapper (build.sh)

### Phase 2 — Pin Map and Sensors ✅
- Full GPIO pin map from BF config + ArduPilot hwdef + schematic + ORQA official PX4 fork
- Dual IMU (MPU6000/ICM42688P on SPI1, ICM42688P on SPI4) with verified rotations (R12/R14)
- DPS310 baro on I2C2, QMC5883 mag on I2C1
- MAX7456 OSD on SPI3, W25Q128FV flash on SPI2
- 11 PWM outputs (8 motors + 3 servos) with DMA
- CAN bus (FDCAN1), SDMMC1, 3 LEDs, buzzer, camera switch
- Wingcore fixed-wing variant added
- Aligned with ORQA official PX4 fork (orqafpv/PX4-Autopilot develop_h743-3030-pro)
- Board ID: 1013
- ArduPilot OrqaF405Pro hwdef fix prepared (patch + PR template)

---

## Blockers

- **Physical hardware required for Phase 3+**: Need ORQA H7 board for flash/boot/sensor validation
- **UART ttyS mapping**: Needs runtime verification on hardware
- **CAN + Timer5 bug**: PX4 bug disables Timer5 outputs when CAN enabled (motors 3-6)

---

## Todos

- [x] Verify HSE frequency (8MHz confirmed)
- [x] Full pin map from schematic + BF + ArduPilot
- [x] IMU rotations verified (R12 SPI1, R14 SPI4)
- [x] Align with ORQA official PX4 fork
- [ ] Confirm ttyS numbering on hardware
- [ ] DPS310 WHO_AM_I verification on hardware
- [ ] Hardware flash + boot test
- [ ] DShot ESC test
- [ ] Flight test

---
*State updated: 2026-03-16*
