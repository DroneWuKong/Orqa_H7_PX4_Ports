# Project State: PX4 Port — Orqa H7 QuadCore

**Last updated:** 2026-03-10
**Session:** Roadmap creation

---

## Project Reference

**Core value:** PX4 boots, dual IMU + baro are correctly mapped, and the quad flies stably in Stabilized mode
**Target hardware:** Orqa H7 QuadCore (STM32H743), 30x30mm FPV stack
**Current focus:** Phase 1 — Scaffold and Build

---

## Current Position

**Phase:** 1 — Scaffold and Build
**Plan:** None yet (planning not started)
**Status:** Not started

```
Progress: [          ] 0%
Phase 1 [.....] Phase 2 [     ] Phase 3 [     ] Phase 4 [     ] Phase 5 [     ]
```

---

## Performance Metrics

| Metric | Value |
|--------|-------|
| Phases total | 5 |
| Phases complete | 0 |
| Requirements mapped | 24/24 |
| Requirements complete | 0/24 |
| Plans written | 0 |
| Plans complete | 0 |

---

## Accumulated Context

### Key Decisions

| Decision | Rationale |
|----------|-----------|
| Coarse granularity → 5 phases | Research proposed 9; compressed to 5 at coarse setting. Phase 2 bundles console + all sensors + UARTs — sequential in practice but same delivery boundary |
| Phase 4 (GPS) depends on Phase 2, not Phase 3 | GPS/mag bring-up is sensor work independent of motor outputs; can proceed after Phase 2 if desired |
| Phase 5 (Flight) depends on both Phase 3 and Phase 4 | Arming and calibration require both motors and GPS/mag |
| Base on Matek H743 Slim | Same MCU family, proven PX4 port, similar peripheral layout |
| DSHOT300 for motor outputs | FPV use case; ESC3030 supports DSHOT; required by project constraints |

### Critical Pitfalls (carry forward to planning)

- HSE crystal is 8MHz (not 16MHz like some reference boards) — must set `STM32_BOARD_XTAL=8000000` in Phase 1
- DMA stream conflicts: SPI1+SPI4+TIM2/3/4/5+UARTs all compete; map explicitly before Phase 3
- Use `icm42688p` driver explicitly (WHO_AM_I=0x47); do not rely on autodetect
- DSHOT timing: APB1 timer input = 240MHz; prescaler=0, period=800 for DSHOT300
- GPIO AF errors: verify each motor pin AF against STM32H743 DS12110 before writing board_config.h

### Research Flags (require live code validation)

- Phase 2/IMU: SPI bus logical numbering and exact `icm42688p start` flag syntax — verify against actual `boards/matek/h743-slim/` source
- Phase 3/DSHOT: DMA burst register offsets and `DMAMAP_TIMx_UP` constants — verify against current `dshot.cpp`
- ICM-42688-P rotation enum integer values (CW270=? CW180=?) — verify against current `enum Rotation` in PX4 source

### Todos

- [ ] Verify Matek H743 Slim HSE frequency from `boards/matek/h743-slim/nuttx-config/include/board.h`
- [ ] Confirm ttyS numbering order from Matek defconfig enable sequence
- [ ] Confirm DPS310 vs DPS368 variant on Orqa board (WHO_AM_I 0x10 vs 0x50)
- [ ] Check W25Q128 PX4 MTD driver name from `src/drivers/mtd/` (v2 scope but useful to note)

### Blockers

None currently.

---

## Session Continuity

To resume after a break:
1. Read this file
2. Read `ROADMAP.md` for phase structure and success criteria
3. Read `REQUIREMENTS.md` for requirement detail and traceability
4. Check which phase is current and whether a plan exists
5. If no plan exists for current phase, run `/gsd:plan-phase N`

---
*State initialized: 2026-03-10*
