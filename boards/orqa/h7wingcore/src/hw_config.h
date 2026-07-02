/**
 * hw_config.h - ORQA H7 QuadCore bootloader configuration
 */

#ifndef HW_CONFIG_H_
#define HW_CONFIG_H_

/* Boot device selection list */
#define USB0_DEV       0x01
#define SERIAL0_DEV    0x02
#define SERIAL1_DEV    0x04

/* 384 KB bootloader reservation, matching mainline ArduPilot's
 * OrqaH7QuadCore hwdef-bl (FLASH_BOOTLOADER_LOAD_KB 384). With the same
 * board id (1204) and load address, PX4 firmware flashes correctly through
 * either this PX4 bootloader or a mainline ArduPilot bootloader. */
#define APP_LOAD_ADDRESS               0x08060000
#define BOOTLOADER_DELAY               3000
#define INTERFACE_USB                  1
#define INTERFACE_USB_CONFIG           "/dev/ttyACM0"
#define BOARD_VBUS                     MK_GPIO_INPUT(GPIO_OTGFS_VBUS)

#define BOOT_DELAY_ADDRESS             0x000001a0
/* 1204 = AP_HW_ORQAH7QUADCORE, registered in the shared board-id registry
 * and used by mainline ArduPilot's OrqaH7QuadCore bootloader (which also
 * loads firmware at 384 KB) — so PX4 images flash through either this PX4
 * bootloader or a mainline AP bootloader. The previous value 1013 collided
 * with AP_HW_MATEKH743. Old FACTORY bootloaders report Orqa-private ids
 * (1185 in arduplane_with_bl_v1.1.hex, 1188 on the orqafpv/ardupilot
 * h7quadcore branch) and will refuse this image with an id mismatch —
 * DFU-install a current bootloader in that case. */
#define BOARD_TYPE                     1204
/* App region: sectors 3..14 (0x08060000..0x081E0000, 1536 KB).
 * Sector 15 is reserved for flash-based params (APP_RESERVATION_SIZE). */
#define BOARD_FLASH_SECTORS            (12)
#define BOARD_FLASH_SIZE               (16 * 128 * 1024)
#define BOARD_FIRST_FLASH_SECTOR_TO_ERASE 3
/* 384 KB reserved: 256 KB for the bootloader gap (app is at sector 3, not
 * sector 1) + 128 KB for the flash-params sector. The PX4 bootloader
 * hardcodes BOOTLOADER_RESERVATION_SIZE=128 KB, so APP_SIZE_MAX (=fw_size)
 * = 2048 - 128 - APP_RESERVATION. With 384 KB this yields exactly 1536 KB,
 * keeping the bootloader's erase/CRC scans inside [0x08060000, 0x081E0000)
 * instead of overrunning the params sector and the end of flash. */
#define APP_RESERVATION_SIZE           (3 * 128 * 1024)

#define OSC_FREQ                       8

#define BOARD_PIN_LED_ACTIVITY         GPIO_nLED_RED
#define BOARD_LED_ON                   0
#define BOARD_LED_OFF                  1

#define SERIAL_BREAK_DETECT_DISABLED   1

#if !defined(ARCH_SN_MAX_LENGTH)
# define ARCH_SN_MAX_LENGTH 12
#endif

#if !defined(APP_RESERVATION_SIZE)
#  define APP_RESERVATION_SIZE 0
#endif

#if !defined(BOARD_FIRST_FLASH_SECTOR_TO_ERASE)
#  define BOARD_FIRST_FLASH_SECTOR_TO_ERASE 1
#endif

#if !defined(USB_DATA_ALIGN)
# define USB_DATA_ALIGN
#endif

#ifndef BOOT_DEVICES_SELECTION
#  define BOOT_DEVICES_SELECTION USB0_DEV|SERIAL0_DEV|SERIAL1_DEV
#endif

#ifndef BOOT_DEVICES_FILTER_ONUSB
#  define BOOT_DEVICES_FILTER_ONUSB USB0_DEV|SERIAL0_DEV|SERIAL1_DEV
#endif

#endif /* HW_CONFIG_H_ */
