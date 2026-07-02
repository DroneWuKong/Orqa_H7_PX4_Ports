# Orqa F405 Pro — PX4 port notes

STM32F405 FPV flight controller. The PX4 target `orqa_f405pro` was adapted
from PX4 v1.15.4's `diatone/mamba-f405-mk2` (an omnibusf4sd-lineage F405
board), remapped to the Orqa F405 Pro pinout.

## Sources
- `ardupilot-fixes/OrqaF405Pro/hwdef.dat` (ArduPilot OrqaF405Pro, in this repo)
- Betaflight `ORQA-F405-PRO.config` (Ai-Project `configs/orqa/`)

## Pin map (STM32F405, 1 MB flash, 8 MHz HSE)
| Function | Pins |
|----------|------|
| IMU (SPI1, CS PA4) | MPU6000 (BF) / ICM42688P (later) — SCK PA5, MISO PA6, MOSI PA7 |
| OSD MAX7456 (SPI2, CS PB12) | SCK PB13, MISO PB14, MOSI PB15 |
| Dataflash W25Q128FV (SPI3, CS PB3) | SCK PC10, MISO PC11, MOSI PB5 |
| Baro DPS310 | I2C1 (PB6/PB7) @ 0x77 |
| Mag | none onboard; external QMC5883 probed on I2C1 |
| RC (GHST) | USART1 (PA9/PA10) = ttyS0 |
| GPS | USART3 (PB10/PB11) = ttyS1 |
| ESC telemetry | UART5 (PD2 RX) = ttyS2 |
| MAVLink / SiK | USART6 (PC6/PC7) = ttyS3 |
| Motors 1-4 | PA3 T2C4, PB0 T3C3, PB1 T3C4, PA2 T2C3 (match the mamba template exactly) |
| Motors 5-8 (board also breaks these out) | PA0 T2C1, PA1 T2C2, PC8 T8C3, PC9 T8C4 — NOT yet in timer_config (4-motor quad config first) |
| Battery | volt PC1 (ADC1_IN11), curr PC3 (ADC1_IN13) |
| LEDs | PA15, PB4 |
| Board ID | 1155 (AP_HW_ORQAF405PRO) |
| USB | 0x35b6:0x0092 (PID provisional — Orqa F405 USB PID not yet confirmed) |

## Status
- Builds clean against PX4 v1.15.4 (`make orqa_f405pro_default`), 94.68% of the
  992 KB app region — F405 is flash-constrained, so the module set is the
  minimal MC/FPV set inherited from the mamba template (no FW/VTOL, no OSD
  driver yet).
- **Not** hardware-validated. IMU rotations (MPU6000 R2 / ICM42688P R12) are
  from the ArduPilot hwdef and must be checked on a board. USB PID unconfirmed.
- Bootloader: uses the classic F405 layout from the template. A dedicated
  `orqa_f405pro_bootloader` target is not built yet; flash via the factory
  ArduPilot bootloader (board id 1155) or an existing F405 bootloader.

## Follow-ups
- Expand to 8 motor outputs (add TIM2_CH1/2 + TIM8_CH3/4).
- Add MAX7456 OSD driver if flash budget allows.
- Confirm USB PID and IMU rotations on hardware.
