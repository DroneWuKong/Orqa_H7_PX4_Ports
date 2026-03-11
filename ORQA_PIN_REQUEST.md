# Pin Information Request — Orqa H7 QuadCore PX4 Port

Hi,

We are porting PX4 to the Orqa H7 QuadCore (STM32H743). We have the board booting and
the firmware compiling successfully. To proceed with sensor bring-up we need the STM32
GPIO pin assignments for the following signals. Net names are confirmed from the
schematics you provided.

---

## 1. IMU — SPI1 (GYRO_1, ICM-42688-P)

| Signal | Net Name | STM32 Pin | Example (for reference) |
|--------|----------|-----------|------------------------|
| Chip Select | SPI1_NSS | ? | PA4 |
| Clock | SPI1_SCK | ? | PA5 |
| MISO | SPI1_MISO | ? | PA6 |
| MOSI | SPI1_MOSI | ? | PA7 |
| Interrupt | GYRO_1_EXTI | ? | PB0 |

---

## 2. IMU — SPI3 (GYRO_2, ICM-42688-P)

| Signal | Net Name | STM32 Pin | Example (for reference) |
|--------|----------|-----------|------------------------|
| Chip Select | SPI3_NSS | ? | PA15 |
| Clock | SPI3_SCK | ? | PB3 |
| MISO | SPI3_MISO | ? | PB4 |
| MOSI | SPI3_MOSI | ? | PB5 |
| Interrupt | GYRO_2_EXTI | ? | PC4 |

---

## 3. Battery Monitoring (ADC)

| Signal | Net Name | STM32 Pin | Notes |
|--------|----------|-----------|-------|
| Voltage sense | VBAT_SENSE or similar | ? | ADC input |
| Current sense | CURR_SENSE or similar | ? | ADC input |

---

## 4. USB (if not standard)

| Signal | Net Name | STM32 Pin | Notes |
|--------|----------|-----------|-------|
| D+ | USB_DP | ? | Usually PA12 on H743 |
| D- | USB_DM | ? | Usually PA11 on H743 |
| VBUS detect | USB_VBUS | ? | Optional |

---

## 5. Status LED(s)

| Signal | Net Name | STM32 Pin | Active High/Low |
|--------|----------|-----------|-----------------|
| LED 1 | ? | ? | ? |
| LED 2 (if present) | ? | ? | ? |

---

## 6. UART / Serial (for GPS — Phase 4, can defer)

| Signal | Net Name | STM32 Pin | Notes |
|--------|----------|-----------|-------|
| GPS TX | ? | ? | UART peripheral number |
| GPS RX | ? | ? | UART peripheral number |

---

## Already Confirmed (no action needed)

- IMU chips: ICM-42688-P on both SPI1 and SPI3
- IMU rotations: SPI1 = 180° CW, SPI3 = 90° CCW
- HSE crystal: 8 MHz
- MCU: STM32H743VIT6
- Battery ADC scale: 1792 (voltage), 220 (current)

---

Any additional information (full schematic, .ioc file, or CubeMX project) would
accelerate the port significantly and is welcome.

Thank you.
