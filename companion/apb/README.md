# APB PX4 logging installation and validation

Start here: [one-command setup and status](QUICKSTART.md). Detailed manual
installation and validation instructions follow below.

This package records PX4 ULog files on the i.MX-owned SD card while keeping
SD writes out of the core telemetry router. It requires the matching APB PX4
firmware from this tree and a separate installation on the Linux companion.
Flashing the FC alone does not install Linux services.

## Data path and limits

```text
STM32 PX4 bounded logger
  → UART4 at 230400 baud → i.MX /dev/ttymxc2
  → existing mavlink-router → loopback UDP 14560
  → supervised recorder → /sdcard/px4/*.ulg
```

Only the existing router owns the UART. The recorder uses a separate process
and lower scheduling priority; missing/full/removed cards do not stop or
restart the core router. Log storage is pinned through an inherited directory
descriptor, so a later unmount cannot redirect writes into the root filesystem.
The supervisor checks the exact mount, SD device type, read-only state, free
space, process errors and log growth. It retries after five seconds and opens
a fresh log after recovery. It never formats cards or deletes old logs.

The SD-only mounting replacement fixes the vendor helper's quiet-command
exit-status bug and premature asynchronous success marker. It serializes mount
events, rejects eMMC, verifies synchronous mount completion and unmounts only
the matching device. USB mounting still uses the preserved vendor helper.
SD mounts use `nosuid,nodev,noexec` without per-write `sync`; the recorder uses
periodic fsync. Sudden power loss can still lose recent data. Stop recording
and unmount cleanly before intentional removal; insertion/removal under load
is a fault to test, not the normal operating procedure.

The firmware selects MAVLink-only logging and 17 rate-limited, instance-zero
topics in [logging_topics.inc](../../boards/orqa/apb/src/logging_topics.inc).
The generated-struct budget is 4768 bytes/s including conservative padding
and ULog data-record headers. The periodic-data gate is 5500 bytes/s; the
nominal ULog wire budget is 8064 bytes/s at the current `MAV_0_RATE=0` setting.
Events, parameters, protocol overhead and bursts consume the remaining budget.
Actual link latency and dropouts still require board tests.

Attitude/rates are sampled at 10 Hz, local position/control outputs at 5 Hz,
global position/status at 2 Hz, and GPS/battery/estimator status at 1 Hz.
This is a compact operational log, not raw IMU, full-rate tuning or estimator
replay. Flight-control and sensor execution rates are unchanged. Saved
`SDLOG_PROFILE` settings and a logger rate-factor override do not expand this
board-specific profile; increasing it requires rebuilding and passing the
budget check. The other boards retain their original logging profiles.

## Before installation

Work on a disarmed bench with propellers removed. Back up parameters, Linux
configuration and existing logs. Keep a known-good FC firmware for rollback.

On the companion, check:

```sh
/usr/bin/mavlink-routerd -V
python3 --version
systemctl cat mavlink-router.service
cat /etc/mavlink-router/main.conf
ls /etc/mavlink-router/config.d
ss -lunp
findmnt -M /sdcard
lsblk -o NAME,TYPE,FSTYPE,SIZE,MOUNTPOINTS
```

Requirements:

- `mavlink-router` v4, pinned upstream commit
  `42529d55b665e0a9a29e424e186f514c56c2e5b5` (the Ai-Project build script uses v4).
- Python 3, `findmnt`, `systemd-mount` and `systemd-umount` on Linux. No Python
  third-party packages are needed by the deployed supervisor.
- Core router loads `/etc/mavlink-router/config.d`. If its service overrides
  the config directory, place the endpoint there instead after review.
- UDP 14560 is unused. There must be only one native ULog consumer; disable
  competing QGC ULog streaming, but do not disable normal QGC telemetry.
- FC `MAV_SYS_ID=1`. If different, set the recorder's `--system-id` in a systemd
  override. ID 2 is reserved by this router's logger; avoid conflicts anywhere
  on the routed network.
- The inspected Scarthgap v1.0.5 mounting helper has SHA-256
  `501cf034fb6afb04f4fb8036139ab9b131d005c19863d522c95a76d8616452f6`.
  The installer rejects unknown/custom versions instead of overwriting them.
- A trusted SD card/log directory with at least 256 MiB free. Cards with
  multiple data partitions need an explicitly chosen partition/rule; this
  package does not guess which one to prefer.

## Install and activate on the bench

Copy this complete directory onto the companion. From that directory:

```sh
sudo python3 install.py
```

The installer backs up the vendor helper to
`/etc/udev/scripts/orqa-drive-mounting.sh.pre-px4-logging` and installs the
SD wrapper, Python programs, recorder unit and an additive router endpoint.
It does not restart services or change the existing main router configuration.
Repeated installation of identical files is allowed; upgrades over modified
files require review. `--root /path/to/staging-root` supports image staging.

Flash the matching `orqa_apb_default.px4` using the established factory-compatible
procedure. In the PX4 console, verify rather than blindly overwrite settings:

```sh
param show MAV_SYS_ID
param show SER_TEL1_BAUD
param show MAV_0_RATE
param show SDLOG_MODE
logger status
mavlink status
```

Expected: ID 1, baud 230400, rate 0, `SDLOG_MODE` not -1, logger backend
`mavlink`. Existing saved parameters survive firmware updates. Correct any
intentional deviations on the bench, save and reboot as appropriate; the
package does not reset calibration or force parameter changes. Streaming uses
MAVLink 2; confirm it in `mavlink status` during recording.

Activation **briefly interrupts telemetry** when the core router is restarted
once to load its new endpoint. Never perform this in flight:

```sh
sudo systemctl daemon-reload
sudo systemctl restart mavlink-router.service
sudo systemctl enable --now orqa-px4-recorder.service
journalctl -u orqa-px4-recorder.service -f
```

For an already-failed SD mount, stop recording and retry the appropriate
`orqa-mount-sd@<partition>.service` after confirming its device identity.
Do not assume `mmcblk0` is the card. The new helper ignores stale vendor
`/tmp/.orqa_mount_sd` markers; they no longer block retries.

The recorder logs before arming (`LogMode=always`) so startup metadata is
available. It maintains a 256 MiB reserve and stops without deleting data
when the reserve is reached. Free space manually after exporting logs.
Use a systemd override for a larger reserve or a non-default FC ID, preserving
all other arguments. Do not lower the reserve below the 32 MiB CLI minimum.

## Verify before flight

```sh
python3 /usr/local/lib/orqa-px4/recorder.py --check
findmnt -M /sdcard
ls -lh /sdcard/px4
journalctl -u orqa-px4-recorder.service --since '10 minutes ago'
journalctl -u mavlink-router.service --since '10 minutes ago'
```

Check growing `.ulg` files, copy one to the host and open it in a ULog parser.
Confirm the expected topic data, flight-controller identity and timestamps.
Then test no-card boot, low space, mount failure, read-only media, card
removal/return and companion restart. Verify command/telemetry latency and
stream drop counters with vision and other normal companion workloads active.
Check prearm-to-armed transitions and two consecutive flights. Do not use
`logger status`'s file-backend dropout counters alone to assess streamed loss;
inspect `mavlink status`, received log continuity and the receiver journal.

The host suite exercises actual native router subprocesses and the production
supervisor with mocked SD identity. It verifies ULog decoding, duplicate and
split packets, alignment after loss, file-open failures, card removal/return
and telemetry surviving recorder shutdown. It does not qualify the physical
SD controller, serial bandwidth under load, media power-loss behavior or flight.

## Roll back

On the disarmed bench, stop and disable only `orqa-px4-recorder.service`.
Move `90-orqa-px4-logging.conf` out of the core router's config directory and
restart the core router once. Restore the verified vendor helper from
`.pre-px4-logging` if required; do not overwrite unrelated later edits.
Keep `/sdcard/px4` intact. Restore the previous FC firmware if desired; no
parameter/calibration reset is required by this package.

## Run the host checks

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_apb_logging.py /path/to/PX4/build/orqa_apb_default
MAVLINK_ROUTER_BIN=/path/to/v4/mavlink-routerd python3 tests/probe_apb_router.py
```

Run these from the repository root. The protocol probe additionally requires
`pymavlink==2.4.49` and `pyulog==1.3.0`; CI builds the pinned native router and
runs it. All protocol sockets bind only to loopback.
