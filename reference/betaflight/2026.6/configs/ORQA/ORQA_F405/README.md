# ORQA F405 Pro target for Betaflight 2026.6

This is the PCB-specific compile-time target for the ORQA F405 Pro flight
controller. It is separate from the PX4 `orqa_f405pro` target and is not a CLI
configuration dump.

## Build

From a Betaflight `2026.6-maintenance` checkout:

```sh
make CONFIG=ORQA_F405 \
  BETAFLIGHT_CONFIG=/path/to/Orqa_H7_PX4_Ports/reference/betaflight/2026.6
```

The default build matches the factory MPU6000 population and its recovered
Betaflight `CW180_DEG` alignment. A later board population may use an
ICM42688P in the same SPI1 position. Build that population explicitly with:

```sh
make CONFIG=ORQA_F405 \
  BETAFLIGHT_CONFIG=/path/to/Orqa_H7_PX4_Ports/reference/betaflight/2026.6 \
  EXTRA_FLAGS=-DORQA_F405_IMU_ICM42688P
```

The ICM42688P build uses `CW0_DEG_FLIP`, corresponding to the ArduPilot/PX4
R12 (`ROTATION_PITCH_180`) mapping. Do not substitute one sensor-population
build for the other without confirming the installed IMU and its orientation.

## Build verification

Both variants compile and link with Arm GNU Toolchain 13.3.Rel1 against:

- Betaflight `2026.6-maintenance` at `9540d2aab7e1db01198e0dd022f2c8fd262bae44`
- `betaflight/config` at `3a406c5c30c20d7c3bc7dd5ed547cca961baf0a9`
- reported firmware version `2026.6.3`

| Variant | FLASH1 | RAM | SHA-256 |
| --- | ---: | ---: | --- |
| MPU6000 | 541,669 bytes | 94,204 bytes | `2D97E40702C3D59DA716D3236636FC446E85C07CF35F34D0BA4DBE27002D6D62` |
| ICM42688P | 542,053 bytes | 94,204 bytes | `36140C09EC0EBFB9F36049EAC7F932E06F5B1C8DA911EECFCEAC0EE2623736FD` |

These hashes identify the locally generated HEX files from the exact source
revisions above. A successful build is not evidence of board-level validation.

## Recovered hardware mapping

- STM32F405, 8 MHz HSE
- SPI1 PA5/PA6/PA7, CS PA4, EXTI PC4: MPU6000 or ICM42688P
- SPI2 PB13/PB14/PB15, CS PB12: MAX7456 analog OSD
- SPI3 PC10/PC11/PB5, CS PB3: W25Q128FV blackbox flash
- I2C1 PB6/PB7: DPS310 at `0x77`; external QMC5883/dashboard
- UART1 PA9/PA10: Ghost receiver
- UART3 PB10/PB11: GPS
- UART5 PD2 RX: ESC telemetry
- UART6 PC6/PC7: external telemetry
- Motors 1-4: PA3, PB0, PB1, PA2
- Servos 1-2: PA0, PA1
- PPM: PC9
- Battery voltage/current: PC1/PC3
- LEDs: PA15/PB4; beeper: PA8
- Camera switch: PB9; USB VBUS detect: PC5

The mapping was cross-checked against the factory Betaflight 4.4.1 dump, the
ArduPilot `OrqaF405Pro` hardware definition, and this repository's PX4 F405
port. The target is software-build validated only until it is checked on the
exact board revision with props removed. Verify the IMU identity/orientation,
DPS310, receiver, GPS, motor order/direction, bidirectional DShot, OSD,
blackbox flash, ADC calibration, ESC telemetry, and camera switch before any
flight use.
