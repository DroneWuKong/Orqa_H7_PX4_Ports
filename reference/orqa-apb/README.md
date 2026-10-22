# Orqa APB / factory firmware reference

Current implementation: [companion/apb](../../companion/apb/README.md) contains
the SD-only mount fix, guarded recorder, conservative FC log profile and
installation/rollback procedure. The investigation entries below retain the
evidence and intermediate findings; their "not yet implemented" statements
describe the investigation stage, not the current source tree. Physical
deployment and qualification are still separate from host testing.

## SD card ownership correction (2026-10-22)

The APB microSD is **i.MX8M Plus/Linux storage**, mounted by Orqa at
`/sdcard`. It is not an STM32 SDMMC bring-up task. Earlier entries below
describe the provisional vendor PX4 definitions; their pin conflicts do not
establish the physical connection of the APB card. Keep STM32 SDMMC disabled.

Evidence inspected:

- `DroneWuKong/Ai-Project`, commit
  `173c89a5bc0697cea636ec02d34b90c944a1d8ef`,
  [`docs/hardware/orqa_dtk_apb_manual_v1_6.md`](https://github.com/DroneWuKong/Ai-Project/blob/173c89a5bc0697cea636ec02d34b90c944a1d8ef/docs/hardware/orqa_dtk_apb_manual_v1_6.md):
  section 4 explicitly places the SD card at Linux `/sdcard`; sections 6 and
  9 describe the FC-to-companion UART connection. This is the repository's
  manual reference, not a newly inspected electrical schematic.
- Orqa APB Scarthgap v1.0.5 SDK target sysroot and recovery image both contain
  `etc/udev/rules.d/automount.rules`, selecting Linux `mmcblk0*`/`mmcblk1*`
  filesystem devices for `orqa-mount-sd@.service`.
- `lib/systemd/system/orqa-mount-sd@.service` invokes
  `etc/udev/scripts/orqa-drive-mounting.sh sdcard ...`; the script uses
  `systemd-mount` with destination `/sdcard`. Do not infer a fixed SD block
  device number from those wildcard rules, or confuse the card with eMMC.

SHA-256 of those three SDK files, in the order above:

```text
cd1657f1daba4f48e97d6bffc3bfbec238caf07ec58434a6440ed8e74c49a5d8  automount.rules
8db3b861cf328ba91ef7ea5d54e6769b443afa3e9d10760a90bcd9c175dd584f  orqa-mount-sd@.service
501cf034fb6afb04f4fb8036139ab9b131d005c19863d522c95a76d8616452f6  orqa-drive-mounting.sh
```

The inspected SDK is stored on GupB under
`/srv/dev-rig/storage/usb-ssd/orqa-sdk/apb-scarthgap-v1.0.5/sysroots/armv8a-orqa-linux/`.
These supplied artifacts were read, not modified or deployed.

### Linux-side SD defects found in the supplied helper

1. `is_mounted()` captures `mountpoint -q` stdout and compares it with `0`.
   Quiet mode produces no output: it must test the command's **exit status**.
   A read-only host reproduction using the mounted `/proc` returns status 0
   from `mountpoint` but takes the helper's "not mounted" branch. Therefore
   its `unmount_sd()` skips its intended unmount call for a mounted path.
2. `mount_sd()` uses `systemd-mount --no-block` and then creates
   `/tmp/.orqa_mount_sd`. Job submission is not proof of a completed mount;
   a later mount failure can leave the marker blocking subsequent attempts.

These are source-level defects, not a diagnosis established on the user's
running APB. Check the installed script/version and service journal before
deploying a fix. Do not patch an archived SDK/image as if that fixes the board.

### What PX4 still needs

The intended path is STM32 PX4 → MAVLink UART4 → i.MX UART3
(`/dev/ttymxc2`, 230400 baud) → ULog receiver → mounted `/sdcard`.
The inspected Ai-Project `apb/deploy/mavlink-router.conf` forwards telemetry
but has no log destination configured. A router connection alone does not
prove flight logs are being recorded. PX4 v1.15.4's logger supports a MAVLink
backend; a compatible receiver must request and reconstruct that log stream.
Do not equate ordinary telemetry `.tlog` recording with PX4 ULog recording.

The remaining work is companion mount reliability and end-to-end log capture,
including UART bandwidth, dropouts, missing/full-card behavior and safe
recovery. Internal-flash parameters and SPI W25 mission storage on the FC
remain separate from the companion card. No new firmware build, hardware
qualification, or successful SD recording is claimed by this correction.

### Logging investigation and host proof (2026-10-22)

**The missing receiver already exists in mavlink-router v4.** Ai-Project's
build script selects that release, commit
`42529d55b665e0a9a29e424e186f514c56c2e5b5`. Its
[`ULog` implementation](https://github.com/mavlink-router/mavlink-router/blob/42529d55b665e0a9a29e424e186f514c56c2e5b5/src/ulog.cpp)
requests `MAV_CMD_LOGGING_START`, acknowledges reliable header packets and
reconstructs `.ulg` files. `MavlinkDialect=auto` selects it for a PX4 heartbeat;
`common` selects it explicitly. Without `[General] Log=...`, the router
does not instantiate a recorder. That option is absent in the inspected
Ai-Project companion configuration. This establishes a missing configuration
in the repository, not the state of the currently installed APB.

The PX4 v1.15.4 application already includes `logger`. Its default backend is
`all` (file and MAVLink), and a MAVLink logging request starts the streaming
backend. `SDLOG_MODE=-1` prevents logger startup and must not be used to mean
"no STM32 SD". For an APB-specific integration, explicitly selecting
`logger -m mavlink` via startup `LOGGER_ARGS` avoids unnecessary local-file
attempts and file-backend free-space checks. No firmware change was made in
this investigation.

**Bandwidth is the other constraint.** In the pinned
[`mavlink_main.cpp`](https://github.com/PX4/PX4-Autopilot/blob/99c40407ffd7ac184e2d7b4b293f36f10fe561ef/src/modules/mavlink/mavlink_main.cpp),
rate zero selects `baud / 20`: 11520 bytes/s at 230400 baud, not unlimited
bandwidth as the existing board-default comment says. ULog's nominal share
is 70% (8064 bytes/s before packet overhead/packet-rate rounding), and PX4
denies streaming below a configured link budget of 5000 bytes/s. The default
log profile includes high-rate topics; a bandwidth-limited profile and
on-hardware measurements are required before claiming dropout-free logging.
Simply increasing the serial baud is not justified by the existing APB
link-loss history. Also, a `logger_topics.txt` file on Linux `/sdcard` is not
visible to STM32 PX4's `/fs/microsd` path.

**Host-only experiment:** compiled unmodified router v4 natively on GupB,
then ran a mock MAVLink 2 PX4 sender through a core router and a separate
recorder router over loopback UDP. Five cases passed:

1. No `Log` option: no log-start request.
2. Normal recording: log-start request, header ACKs, duplicate suppression,
   exact reconstructed bytes; telemetry forwarding continues after recorder
   termination.
3. A ULog record split across two MAVLink packets reconstructs correctly.
4. After a simulated packet gap, a valid `first_message_offset` restores
   message alignment. This is **not** recovery of lost samples.
5. An initial file-open failure disables recording; fixing the path alone
   does not restart it. The recorder needs to be restarted.

The three generated `.ulg` files were also parsed independently with
`pyulog`, recovering the expected test dataset and both sample values.
The normal case intentionally used an ordinary, unmounted directory and
the router wrote there successfully: **the router does not enforce SD mount
presence**. This reproduces the risk of filling the companion root filesystem
when `/sdcard` is just a directory.

Evidence remains on GupB in `/tmp/apb-logging-investigation.3yZyQs/`:
`probe_logging.py`, per-case configurations/logs/output files, and the pinned
router source/build. Probe SHA-256:
`f9bd5c02654feb711494b25009b02a767250a97de261507743cbd1a37b3999a7`.
These are synthetic protocol tests, not a PX4 flight simulation or physical
UART/SD qualification.

**Recommended implementation, not yet deployed:** leave the core router as
the sole owner of `/dev/ttymxc2`; add a loopback endpoint for a separate ULog
recorder process. Gate that recorder on the actual writable SD mount, monitor
free space and failures, and restart only the recorder on recovery. Native
ULog performs synchronous file writes in its routing loop, so putting it in
the core router would couple slow SD writes to telemetry forwarding. Separate
processes isolate that disk-I/O failure, but do not remove shared UART bandwidth
or CPU constraints. Do not condition or stop the core telemetry service on SD
availability. Graceful recorder shutdown must stop the FC log stream; abrupt
failure/recovery also needs testing. Router v4 uses logger system ID 2, which
must not conflict with other participants. Keep log auto-deletion disabled
until a retention policy is approved.

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
