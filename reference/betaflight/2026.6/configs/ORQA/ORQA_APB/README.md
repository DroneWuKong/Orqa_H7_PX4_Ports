# ORQA APB Betaflight 2026.6 target

This is a native Betaflight configuration target for the STM32H743 flight
controller integrated into the ORQA DTK APB. It is not the standalone ORQA H7
QuadCore target and it is not a CLI dump.

The default build matches ORQA's original APB sensor population:

- SPI1 MPU6000, PX4 rotation R12 (`CW0_DEG_FLIP`)
- SPI4 ICM42605, PX4 rotation R12 (`CW0_DEG_FLIP`)

Later APB hardware uses ICM42688P devices and a different SPI4 orientation.
Select that population explicitly with `EXTRA_FLAGS=-DORQA_APB_IMU_ICM42688P`;
it uses R12 on SPI1 and R14 (`CW90_DEG_FLIP`) on SPI4. The target deliberately
does not probe both SPI4 chip types under one static alignment, because doing so
could accept a detected gyro with the wrong axes.

## Build

From a Betaflight `2026.6-maintenance` checkout:

```sh
make CONFIG=ORQA_APB \
  BETAFLIGHT_CONFIG=/path/to/Orqa_H7_PX4_Ports/reference/betaflight/2026.6
```

Later ICM42688P APB revision:

```sh
make CONFIG=ORQA_APB \
  BETAFLIGHT_CONFIG=/path/to/Orqa_H7_PX4_Ports/reference/betaflight/2026.6 \
  EXTRA_FLAGS=-DORQA_APB_IMU_ICM42688P
```

## APB-specific defaults

- UART3 PD8/PD9: Ghost receiver
- UART4 PC10/PC11: internal i.MX8M Plus link (field configuration is MAVLink
  telemetry at 230400; assign this in Betaflight after flashing)
- UART6 PC6/PC7: external telemetry / SiK / gimbal
- UART7 PE8/PE7: GPS
- UART8 PE1/PE0: ESC telemetry
- I2C2 PB10/PB11: DPS310 barometer at `0x77`
- SPI2 PB13/PB14/PB15, CS PB12: W25Q128FV blackbox flash
- SPI3 PB3/PB4/PD6, CS PA15: MAX7456 analog OSD
- Motors 1-8: PD13, PD12, PA1, PA0, PA2, PA3, PB1, PB0
- Servos 1-3: PE6, PE5, PD14
- Camera switch: PD0
- USB VBUS detect: PE2

SDMMC2 is intentionally disabled. ORQA's public initial PX4 mapping overlaps
the SPI2 flash pins, SPI3 OSD pins, and PC1 current ADC, so enabling it without
board-revision schematics would silently break known peripherals.

## Flash layout warning

This target uses Betaflight's normal STM32H743 internal-flash layout. The APB's
factory ArduPilot bootloader expects an application at `0x08060000` and cannot
directly install the normal Betaflight HEX. Use STM32 DFU/SWD and follow a
verified recovery procedure; do not assume the factory bootloader can upload
this image. Hardware validation is still required before flight.
