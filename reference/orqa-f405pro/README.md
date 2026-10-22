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
| Motors 1-4 | PA3 T2C4, PB0 T3C3, PB1 T3C4, PA2 T2C3 |
| Motors 5-8 | PA0 T2C1, PA1 T2C2, PC8 T8C3, PC9 T8C4 |
| Battery | volt PC1 (ADC1_IN11), curr PC3 (ADC1_IN13) |
| LEDs | PA15, PB4 |
| Board ID | 1155 (AP_HW_ORQAF405PRO) |
| USB | 0x35b6:0x0092 (PID provisional — Orqa F405 USB PID not yet confirmed) |

## Status
- Builds clean against PX4 v1.15.4 (`make orqa_f405pro_default`): 951,729 of
  999,424 bytes (95.23%) in the corrected 976 KB application region.
- The app starts at `0x0800C000`, matching the factory bootloader's 48 KB
  reservation, and uses a 976 KB application region.
- The board has no microSD socket. SPI2 drives the MAX7456 OSD; SPI3 drives
  the W25Q128 dataflash, which stores parameters and waypoints through PX4's
  MTD manifest.
- All eight motor outputs and the MAX7456 OSD driver are enabled.
- **Not** hardware-validated. IMU rotations (MPU6000 R2 / ICM42688P R12) are
  from the ArduPilot hwdef and must be checked on a board. USB PID unconfirmed.
- Bootloader: a dedicated
  `orqa_f405pro_bootloader` target is not built yet; flash via the factory
  ArduPilot bootloader (board id 1155) or an existing F405 bootloader.

## Follow-ups
- Confirm the factory USB PID and IMU rotations on hardware.
- Verify external-flash parameter persistence, OSD output, and all eight motor
  channels on a physical board.
