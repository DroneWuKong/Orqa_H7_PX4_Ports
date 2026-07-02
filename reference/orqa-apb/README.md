# Orqa APB / factory firmware reference

## `hwdef-bl.dat`
ArduPilot bootloader hardware definition for the Orqa DTK APB FC
(`APJ_BOARD_ID AP_HW_ORQAAPB`), as provided by Orqa. Key facts:

- STM32H743, 8 MHz HSE, 2048 KB flash
- Firmware load offset: **384 KB** (`FLASH_BOOTLOADER_LOAD_KB 384` → app at 0x08060000)
- USB: VID `0x35b6` (Orqa), PID `0x0090`, manufacturer string "Orqa"
- `ENABLE_DFU_BOOT 1` — the bootloader can reboot into STM32 system DFU (0x0483:0xdf11)
- CS pins match the H7 QuadCore exactly: GYRO1=PA4, GYRO2=PE11, OSD1=PA15, FLASH1=PB12, CAM_SW=PD0
- Bootloader LED PA8, serial order: USB (OTG1) only

## `arduplane_with_bl_v1.1.hex` (not committed — 5 MB factory image)
Facts extracted from the factory image supplied with the standalone H7 FC:

- Layout: bootloader at 0x08000000, app at **0x08060000** (matches the 384 KB offset)
- App identifies as **"OrqaH743Wing", ArduPlane V4.5.7 (b2246a2f)**
- USB VID/PID in BOTH bootloader and app: `0x35b6:0x0091`
- Bootloader `board_info` struct at flash 0x08009560: **board_type=1185 (0x4A1)**,
  board_rev=0, fw_size=0x1A0000 (1664 KB = 2048−384)
- NOTE: mainline ArduPilot `board_types.txt` now assigns 1185 to
  `AP_HW_X-MAV-AP-F405Mini` — Orqa's allocation was private and predates it.
  Mainline has since registered `AP_HW_ORQAH7QUADCORE = 1204`, which this
  port uses for the quadcore/wingcore targets.
- The numeric value of `AP_HW_ORQAAPB` (PID 0x0090 variant) is UNCONFIRMED;
  the PX4 `orqa_apb` target provisionally uses 1185 pending confirmation
  from Orqa. If the factory bootloader rejects an upload with a board-id
  mismatch, correct `boards/orqa/apb/firmware.prototype` and
  `boards/orqa/apb/src/hw_config.h` together.
