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

## AI Wingman drive findings (2026-07-02)

- The Drive copy of `hwdef-bl.dat` is byte-identical to the one in this
  directory — no newer revision exists there.
- `wingman-apb-deploy-guide-v2` (Drive): the companion-side wingman service
  reads the FC over the APB's internal bridge at `udp://127.0.0.1:14540`
  and requires `MAV_0_MODE=2` (ONBOARD) + `MAV_0_RATE=0` on PX4. These are
  now board defaults in `boards/orqa/apb/init/rc.board_defaults`.
- `arducopter4.5_with_bl_MRM2-10_AI_v1.1.hex` (Drive, 5.2 MB, private):
  factory ArduCopter+bootloader image for the MRM2-10 AI (APB-based
  platform). Its bootloader should carry the true `AP_HW_ORQAAPB` board ID
  (expected USB PID 0x0090). Too large to pull through the Drive API in a
  session; extract locally with:

      python3 - arducopter4.5_with_bl_MRM2-10_AI_v1.1.hex <<'PY'
      import struct, sys
      data, base = {}, 0
      for line in open(sys.argv[1]):
          if not line.startswith(':'): continue
          b = bytes.fromhex(line.strip()[1:])
          if b[3] == 4: base = ((b[4]<<8)|b[5]) << 16
          elif b[3] == 0:
              for i, v in enumerate(b[4:4+b[0]]): data[base+((b[1]<<8)|b[2])+i] = v
      img = bytearray(b'\xff'*(max(data)-0x08000000+1))
      for a, v in data.items(): img[a-0x08000000] = v
      # board_info struct: board_type(u32), 0, fw_size(u32) — fw_size = 0x1A0000
      for off in range(0, 0x60000-12, 4):
          t, r, f = struct.unpack_from('<III', img, off)
          if f == 0x1A0000 and r == 0 and 0 < t < 65536:
              print(f"board_type={t} at flash 0x{0x08000000+off:08x}")
      PY

  In the ArduPlane Wing image this prints `board_type=1185`; whatever it
  prints for the MRM2-10 AI image is the value to put in
  `boards/orqa/apb/firmware.prototype` + `src/hw_config.h`.

## orqafpv/ardupilot fork findings (2026-07-02, user-provided link)

- **master** `OrqaH7QuadCore/hwdef-bl.dat`: `APJ_BOARD_ID AP_HW_ORQAH7QUADCORE`
  (= **1204** in the registry), `FLASH_BOOTLOADER_LOAD_KB 384`, no custom USB
  IDs. Mirrors mainline ArduPilot.
- **h7quadcore branch** `OrqaH7QuadCore/hwdef-bl.dat`: same file with
  `USB 0x35b6:0x0090 "Orqa"` and `AP_HW_ORQAH7QUADCORE = 1188` in that
  branch's board_types.txt. This is the direct lineage of the APB hwdef-bl
  in this directory — identical except the board-id symbol was changed to
  `AP_HW_ORQAAPB` (numeric value not present in any public tree).
- Orqa-private id cluster so far: 1185 (H743Wing factory bl), 1188
  (h7quadcore branch); `AP_HW_ORQAAPB` is likely nearby but unconfirmed.
- Consequence adopted in this repo: since mainline AP's OrqaH7QuadCore
  bootloader is 1204 @ 384 KB, ALL PX4 targets here now link at 0x08060000
  (1536 KB app, params in sector 15) so a matching-id image can never be
  placed at the wrong address by an AP bootloader, and quadcore/wingcore
  PX4 firmware flashes directly through a mainline AP bootloader.

## orqafpv/PX4-Autopilot fork findings (2026-07-02, user-provided link)

Branch **`develop_APB-initial`** contains ORQA's own PX4 APB target
(`boards/orqa/h743-APB`, plus `h743-3030-pro`). Authoritative deltas adopted
into `boards/orqa/apb`:

- **UART4 (PC10/PC11, `GPIO_UART4_*_4`) is the i.MX8M Plus bridge** —
  commented "IMX" in their board.h; TEL1=/dev/ttyS1 @ 115200
  (`SER_TEL1_BAUD 115200` in their defaults). Serial roles: USART3 RC,
  UART4 TEL1/IMX, USART6 TEL2 (SiK/gimbal, console), UART7 GPS (ttyS3),
  UART8 ESC telem (ttyS4).
- **SDMMC2 instead of SDMMC1** (UART4 owns SDMMC1's D2/D3 pins). Their
  SDMMC2 pin picks overlap SPI2 dataflash (PB14/PB15), SPI3 OSD (PB3/PB4),
  and the PC1 current ADC — inconsistencies of an "initial" branch;
  carried over verbatim with a warning comment pending hardware truth.
- **Sensors**: SPI1 MPU6000 R12 (their fallback mpu6500 has no driver
  enabled; we fall back to ICM42688P R12 per QuadCore rev history);
  SPI4 ICM42605 **R12** / ICM42688P **R14** (rotation differs per chip).
- **SPI pin fixes for ALL targets**: their board.h exposed two latent bugs
  in our QuadCore-derived board.h — SPI4 used `_2` variants
  (PE2/PE5/PE6, colliding with VBUS + TIM15 servos) instead of `_1`
  (PE12/PE13/PE14), and SPI3 (OSD) had no pin defines at all. Verified
  against the NuttX stm32h7x3xx pinmap; note their `/* PB5 */` comment on
  `GPIO_SPI3_MOSI_1` is wrong — the token resolves to **PD6** (matching
  this repo's cross-validated pin notes).
- Their PX4 identity: board id **1013** (the Matek H743 collision — origin
  of this port's old value), app @ 0x08020000, `image_maxsize` 1920K,
  summary "OrqaH743", USB CDCACM `0x35b6:0x0090` (matches our target).
  We intentionally diverge on id/layout (1185-provisional @ 0x08060000).

## Companion UART — CONFIRMED (2026-07-02, Ai-Project apb/deploy)

The FC↔SOC MAVLink link is fully pinned down from two independent files in
`DroneWuKong/Ai-Project` (`apb/deploy/`):

- `mavlink-router.conf`: `[UartEndpoint fc] Device=/dev/ttymxc2 Baud=230400`
  — SOC side is i.MX8M Plus **UART3** (`/dev/ttymxc2`), bridged to
  `udp://127.0.0.1:14540` (wingman-apb) and `:14541` (wingman-vio).
- `configs/orqa_mrm2_10f_arducopter.param`: `SERIAL4_PROTOCOL=2` (MAVLink2),
  `SERIAL4_BAUD=230` with the inline note "matches APB mavlink-router
  /dev/ttymxc2". SERIAL1=SiK/RFD 57600, SERIAL2=GPS, SERIAL3=GHST RC.
- `deploy/gpio-uart-fc.sh`: the SOC UART3 is behind a GPIO mux —
  gpiochip3 line 13 (UART3_SEL_FC=1) + line 0 (UART3_FC_EN=0) route it to
  the H743. Asserted by mavlink-router.service ExecStartPre.

**Baud is 230400, field-confirmed. 921600 caused FC link loss after
reflashes** (noted in both mavlink-router.conf and the param file). The PX4
APB target sets `SER_TEL1_BAUD 230400` on TEL1 (FC UART4, PC10/PC11)
accordingly. This resolves open question APB-2.

Known SOC-side gotcha (not a PX4 concern, but relevant to bring-up): an
imx-sdma RX-DMA boot race can leave the SOC's ttymxc2 RX dead on cold boot
(`mavlink-router-rxdma-recover.{sh,service}` restarts the router when the
signature appears).

## AP_HW_ORQAAPB = 1189 — CONFIRMED (2026-07-02, MRM2-10 AI factory hex)

Extracted from `arducopter4.5_with_bl_MRM2-10_AI_v1.1.hex` (the factory
ArduCopter+bootloader image for the APB-based MRM2-10 AI platform):

- Bootloader `board_info` struct @ flash **0x08004970** =
  `{board_type=1189 (0x4A5), board_rev=0, fw_size=0x1A0000}`.
- Same image carries the literal string **"ORQAAPB"**, "ArduCopter V4.5.7
  (07d727a0)", and USB descriptors **0x35b6:0x0090** (the APB PID) — so 1189
  is unambiguously `AP_HW_ORQAAPB`, not a sibling board.
- App linked at **0x08060000** (384 KB), consistent with the hwdef-bl.

`boards/orqa/apb` now uses BOARD_TYPE / board_id **1189** (was provisionally
1185). This is the id the factory APB bootloader validates uploads against,
so PX4 `.px4` images built with it will be accepted by the on-board
ArduCopter/ArduPilot bootloader. Resolves open question APB-1.

Provenance note: Orqa's private id cluster is now fully mapped — 1185
(H743Wing arduplane), 1188 (OrqaH7QuadCore, orqafpv fork branch), 1189
(ORQAAPB). None collide with each other; 1185/1188/1189 do overlap unrelated
mainline ArduPilot ids (X-MAV etc.), which is expected for a vendor-private
allocation and harmless as long as PX4 matches the factory bootloader.
