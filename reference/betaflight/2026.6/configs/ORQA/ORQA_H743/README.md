# ORQA H7 QuadCore target for Betaflight 2026.6

This is the PCB-specific compile-time target for the standalone ORQA H7
QuadCore flight controller. It is not the ORQA APB target and it is not a CLI
configuration dump.

Betaflight 2026.6 separates MCU targets from PCB configurations. Build this
board with:

```sh
make configs
make CONFIG=ORQA_H743
```

For an external copy of this config repository, point `BETAFLIGHT_CONFIG` at
the directory containing `configs/`:

```sh
make CONFIG=ORQA_H743 BETAFLIGHT_CONFIG=/path/to/orqa-betaflight-2026.6
```

The pinout and defaults were recovered from the factory Betaflight
configuration and cross-checked against the ORQA PX4 port and mainline
ArduPilot `OrqaH7QuadCore` hardware definition. Two corrections are
intentional:

- the physical T2/R2 pads use STM32 USART3 on PD8/PD9;
- the second status LED is PA10, not PA11, because PA11 is USB D-.

The generated firmware compiles cleanly, but it still requires a hardware
bench test before flight. Verify both gyros, DPS310 at address `0x77`, receiver,
motor order/direction, bidirectional DShot, OSD, flash, SD card, GPS, ESC
telemetry, and the PD0 camera switch with props removed.
