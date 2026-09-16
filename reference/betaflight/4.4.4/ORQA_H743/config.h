/*
 * ORQA H7 QuadCore board configuration for Betaflight 4.4.
 *
 * This is the PCB-specific compile-time configuration.  Betaflight includes
 * it through target.h; it is intentionally separate from a unified-target
 * CLI .config file.
 */

#pragma once

#define USE_TARGET_CONFIG

#define TARGET_BOARD_IDENTIFIER "OQH7"
#define USBD_PRODUCT_STRING      "ORQA H7 QuadCore"

/* Status LEDs.  PA11 is USB D-, so the second LED is PA10 (not PA11). */
#define LED0_PIN                 PA8
#define LED1_PIN                 PA10
#define LED2_PIN                 PD11

#define USE_BEEPER
#define BEEPER_PIN               PE9
#define BEEPER_INVERTED
#define BEEPER_PWM_HZ            4000

/* SPI1: primary ICM42688P. */
#define USE_SPI
#define USE_SPI_DEVICE_1
#define SPI1_SCK_PIN             PA5
#define SPI1_MISO_PIN            PA6
#define SPI1_MOSI_PIN            PA7

/* SPI2: W25Q128FV blackbox flash. */
#define USE_SPI_DEVICE_2
#define SPI2_SCK_PIN             PB13
#define SPI2_MISO_PIN            PB14
#define SPI2_MOSI_PIN            PB15

/* SPI3: MAX7456 OSD. */
#define USE_SPI_DEVICE_3
#define SPI3_SCK_PIN             PB3
#define SPI3_MISO_PIN            PB4
#define SPI3_MOSI_PIN            PD6

/* SPI4: secondary ICM42688P. */
#define USE_SPI_DEVICE_4
#define SPI4_SCK_PIN             PE12
#define SPI4_MISO_PIN            PE13
#define SPI4_MOSI_PIN            PE14

#define USE_GYRO
#define USE_ACC
#define USE_EXTI
#define USE_GYRO_EXTI
#define USE_MPU_DATA_READY_SIGNAL
#define ENSURE_MPU_DATA_READY_IS_LOW

#define USE_GYRO_SPI_ICM42688P
#define USE_ACC_SPI_ICM42688P

#define GYRO_1_SPI_INSTANCE      SPI1
#define GYRO_1_CS_PIN            PA4
#define GYRO_1_EXTI_PIN          PC3
#define GYRO_1_ALIGN             CW270_DEG

#define GYRO_2_SPI_INSTANCE      SPI4
#define GYRO_2_CS_PIN            PE11
#define GYRO_2_EXTI_PIN          PE10
#define GYRO_2_ALIGN             CW180_DEG

#define GYRO_CONFIG_USE_GYRO_DEFAULT GYRO_CONFIG_USE_GYRO_BOTH

#define USE_FLASHFS
#define USE_FLASH_TOOLS
#define USE_FLASH_M25P16
#define USE_FLASH_W25Q128FV
#define FLASH_SPI_INSTANCE       SPI2
#define FLASH_CS_PIN             PB12
#define ENABLE_BLACKBOX_LOGGING_ON_SPIFLASH_BY_DEFAULT

#define USE_MAX7456
#define MAX7456_SPI_INSTANCE     SPI3
#define MAX7456_SPI_CS_PIN       PA15

/* I2C1 is external (compass/dashboard); I2C2 carries the onboard DPS310. */
#define USE_I2C
#define USE_I2C_DEVICE_1
#define I2C_DEVICE_1             I2CDEV_1
#define I2C1_SCL                 PB6
#define I2C1_SDA                 PB7

#define USE_I2C_DEVICE_2
#define I2C_DEVICE_2             I2CDEV_2
#define I2C2_SCL                 PB10
#define I2C2_SDA                 PB11

#define USE_MAG
#define USE_MAG_QMC5883
#define MAG_I2C_INSTANCE         I2CDEV_1

#define USE_BARO
#define USE_BARO_DPS310
#define DEFAULT_BARO_DPS310
#define BARO_I2C_INSTANCE        I2CDEV_2

/* USB FS: PA11/PA12 data, PA9 VBUS sense. */
#define USE_VCP
#define USE_USB_DETECT
#define USB_DETECT_PIN           PA9

/* Exposed serial ports.  The pads backed by PD8/PD9 are MCU USART3. */
#define USE_UART3
#define UART3_TX_PIN             PD8
#define UART3_RX_PIN             PD9

#define USE_UART6
#define UART6_TX_PIN             PC6
#define UART6_RX_PIN             PC7

#define USE_UART7
#define UART7_TX_PIN             PE8
#define UART7_RX_PIN             PE7

#define USE_UART8
#define UART8_TX_PIN             PE1
#define UART8_RX_PIN             PE0

#define SERIAL_PORT_COUNT        5
#define SERIALRX_UART            SERIAL_PORT_USART3
#define SERIALRX_PROVIDER        SERIALRX_GHST

/* microSD on SDMMC1, four-bit mode. */
#define USE_SDCARD
#define USE_SDCARD_SDIO
#define SDCARD_DETECT_PIN        NONE
#define SDIO_DEVICE              SDIODEV_1
#define SDIO_USE_4BIT            true
#define SDIO_CK_PIN              PC12
#define SDIO_CMD_PIN             PD2
#define SDIO_D0_PIN              PC8
#define SDIO_D1_PIN              PC9
#define SDIO_D2_PIN              PC10
#define SDIO_D3_PIN              PC11

/* Battery voltage/current sensing. */
#define USE_DMA
#define ADC1_DMA_OPT             8
#define ADC3_DMA_OPT             9
#define USE_ADC
#define USE_ADC_INTERNAL
#define VBAT_ADC_PIN             PC0
#define CURRENT_METER_ADC_PIN    PC1
#define DEFAULT_VOLTAGE_METER_SOURCE VOLTAGE_METER_ADC
#define DEFAULT_CURRENT_METER_SOURCE CURRENT_METER_ADC
#define VBAT_SCALE_DEFAULT       112
#define CURRENT_METER_SCALE_DEFAULT 108

/* Camera switch. */
#define USE_PINIO
#define USE_PINIOBOX
#define PINIO1_PIN               PD0

#define DEFAULT_RX_FEATURE       FEATURE_RX_SERIAL
#define DEFAULT_FEATURES         (FEATURE_TELEMETRY | FEATURE_OSD | FEATURE_GPS)

#define USE_ESCSERIAL

#define TARGET_IO_PORTA          0xffff
#define TARGET_IO_PORTB          0xffff
#define TARGET_IO_PORTC          0xffff
#define TARGET_IO_PORTD          0xffff
#define TARGET_IO_PORTE          0xffff
#define TARGET_IO_PORTF          0xffff
#define TARGET_IO_PORTG          0xffff

#define USABLE_TIMER_CHANNEL_COUNT 11
#define USED_TIMERS (TIM_N(1) | TIM_N(2) | TIM_N(3) | TIM_N(4) | TIM_N(5) | TIM_N(15))
