# PX4 Port — Orqa H7 QuadCore

## What This Is

A PX4 firmware port for the Orqa H7 QuadCore flight controller (STM32H743, 30x30mm). The goal is to create a complete, flight-validated PX4 board target derived from the Matek H743 Slim, ultimately suitable for upstream contribution to the PX4 project. Intended use case is FPV freestyle/racing quadcopters.

## Core Value

PX4 boots, all critical hardware (dual IMU, baro, UARTs, motors) is correctly mapped, and the quad flies stably in Stabilized/Acro mode.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Board target builds successfully from PX4 source
- [ ] ICM-42688 dual IMU detected and functional (SPI1 + SPI4)
- [ ] DPS310 barometer detected and functional (I2C2)
- [ ] All 8 motor outputs functional with DSHOT
- [ ] UART3, UART6, UART7, UART8 correctly assigned
- [ ] USB console / MAVLink works
- [ ] QGroundControl connects and shows sensor data
- [ ] GPS + magnetometer functional (UART7 + I2C1)
- [ ] Quad flies in Stabilized mode
- [ ] Port contributed upstream to PX4 repository

### Out of Scope

- iNav / Betaflight configuration — already working, not this project
- MAX7456 OSD + dual camera switching (v1) — deferred to v2 for ISR use case (thermal + RGB platforms)
- Assisted flight modes (Position Hold, Loiter) — GPS bring-up is v1, mode validation deferred to v2

## Context

**Board:** Orqa H7 QuadCore (SKU 6234)
- MCU: STM32H743 @ 480MHz, ARM Cortex-M7
- IMU: ICM-42688 × 2 (dual gyro)
  - Gyro 1: SPI1, CS=PA4, EXTI=PC3, align=CW270
  - Gyro 2: SPI4, CS=PE11, EXTI=PE10, align=CW180
- Barometer: DPS310 on I2C2 (SCL=PB10, SDA=PB11), addr 0x77
- OSD: MAX7456 on SPI3 (not used by PX4)
- Flash: W25Q128FV on SPI2, CS=PB12 (blackbox)
- HSE crystal: 8MHz
- SD card: present (microSD)
- CAN bus: present

**Pin assignments (from Betaflight config):**
- Motors: M1=PD12, M2=PD13, M3=PA1, M4=PA0, M5=PA2, M6=PA3, M7=PB1, M8=PB0
- Timers: TIM4 (M1/M2), TIM2 (M3/M4), TIM5 (M5/M6), TIM3 (M7/M8)
- Servos: S1=PE6 TIM15CH2, S2=PE5 TIM15CH1
- UART3: TX=PD8, RX=PD9 (VTx/receiver connector)
- UART6: TX=PC6, RX=PC7 (SIK telemetry connector)
- UART7: TX=PE8, RX=PE7 (GPS connector + I2C1 for mag)
- UART8: TX=PE1, RX=PE0 (ESC telemetry)
- I2C1: SCL=PB6, SDA=PB7 (magnetometer)
- I2C2: SCL=PB10, SDA=PB11 (barometer)
- Beeper: PE9, TIM1CH1
- LED1=PA8, LED2=PA11, LED3=PD11
- USB detect: PA9
- ADC: VBAT=PC0, CURR=PC1
- Voltage scale: 112/1/12 ratio; Current scale: 108

**PX4 port status:** Listed as "On Hold" in Orqa's own firmware table (manual v1.1). No official upstream PX4 target exists yet.

**Basis target:** Matek H743 Slim — same STM32H743 MCU family, similar peripheral layout.

**Betaflight config available:** `betaflight_4.4.1_STM32H743_ORQAH7QUADCORE.zip` — contains full pin/timer/DMA assignments as reference.

## Constraints

- **Firmware**: PX4 only — Betaflight/iNav already work, this project is exclusively PX4
- **Target hardware**: 30x30mm FPV stack with Orqa ESC3030
- **ESC protocol**: DSHOT (board uses DSHOT300 bidir in Betaflight; PX4 must match)
- **Upstream goal**: Port must meet PX4 contribution standards (CMake, nuttx config, etc.)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Base on Matek H743 Slim target | Same MCU family, community-proven PX4 port, similar peripheral count | — Pending |
| Dual IMU (both ICM-42688) | Board has two identical gyros; PX4 supports dual IMU for redundancy | — Pending |
| DSHOT for motor output | FPV use case, ESC3030 supports DSHOT, better than PWM for acro | — Pending |
| GPS in v1 scope | User confirmed GPS required; UART7 + I2C1 mag both available on board | — Pending |

---
*Last updated: 2026-03-10 after initialization*
