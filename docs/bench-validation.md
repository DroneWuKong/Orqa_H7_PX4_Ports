# Storage bench validation

Build success is not a hardware test. Record board model/revision, firmware
manifest, SD card model, console output and the outcome of each test. Remove
propellers before powering a flight controller on the bench. Save parameters
and missions through QGroundControl before changing firmware.

## All boards: onboard flash

In QGroundControl's MAVLink console, run:

```text
ver all
mtd status
dataman status
param status
```

Expect a W25 device and a 262144-byte `/fs/mtd_waypoints` partition. F405 must
also report a 65536-byte `/fs/mtd_params` partition. H7 parameters remain in
internal flash; there should be no H7 `/fs/mtd_params` partition. With
`SYS_DM_BACKEND=0`, dataman must report `/fs/mtd_waypoints`, not RAM.

Using QGroundControl, upload a small mission, fence and rally points. Download
them, disconnect power, reconnect, then download and compare again. Repeat
with the SD card absent on QuadCore/Wingcore. Change one harmless parameter
(for example the vehicle name through the GCS if supported, or a recorded
telemetry setting), save, fully power-cycle and verify it, then restore it.
Do not treat a soft reboot alone as proof of persistence.

Record and investigate any W25 attach, partition registration, parameter
import/save or dataman seek/write error. A missing chip must remain an error;
do not mark this test passed because the controller otherwise boots. Avoid
`mtd erase` or `mtd rwtest` on a board containing settings you need to retain.

## QuadCore/Wingcore: SD card

Use a backed-up, FAT32 card inserted before power-on. There is no confirmed
card-detect GPIO: hot removal and insertion are not supported. Run:

```text
ls /dev/mmcsd0
mount
ls /fs/microsd
sd_bench -r 5 -d 2000 -v
sd_bench -r 5 -d 2000 -v -u
logger status
```

`sd_bench` creates and removes its benchmark file on the SD card. Both aligned
and unaligned verification passes must complete without read/write or data
mismatch errors. Record throughput and maximum write latency; a mean rate alone
does not establish reliable logging. After enabling logging through the normal
PX4 logger configuration, verify a ULog can be downloaded and parsed and inspect
logger dropouts during a sustained bench run.

Power off, remove the card, and boot again: internal parameters and W25 missions
must survive. Reinsert only while powered off and repeat. Check multiple card
models and both USB and normal board power.

The patched startup does not format on a failed mount. Test an unsupported or
unmountable **disposable test card** and verify its contents remain unchanged
and the console reports the mount failure. Format new cards as FAT32 on a host.
PX4's explicit `.format` marker remains supported on a mountable card and will
erase that card when requested; do not create it during preservation tests.

## Remaining hardware checks

After storage passes, verify both IMUs and their orientations, ADC scaling,
UART routing, OSD, PWM/DShot outputs and CAN concurrently with logging. APB's
companion UART remains at 230400 baud. APB SD stays disabled until a verified
schematic resolves the published pin conflicts. None of these checks is
established by the host regression tests or seven-target build matrix.
