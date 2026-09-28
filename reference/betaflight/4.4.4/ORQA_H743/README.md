# ORQA H7 QuadCore Betaflight target

This directory is a PCB-specific source target for the standalone ORQA H7
QuadCore flight controller. It is not the ORQA APB target and it is not a CLI
dump.

Build against Betaflight `4.4-maintenance`. The compile check recorded here used
commit `3f62795f389466341ba275037b14c1886ae6dc00` (Betaflight 4.4.4):

```sh
make TARGET=ORQA_H743
```

The target also passes a full warnings-as-errors build:

```sh
make TARGET=ORQA_H743 EXTRA_FLAGS=-Werror
```

The resulting Intel HEX has SHA-256
`ce6dd9718cf224eeb37d3a0e2c6ee6b02f5576f0be953bce650652a77d1e955f`.

`config.h` contains the peripheral and pin definitions requested by the board
port. Betaflight itself enters a target through `target.h`, so `target.h`
includes `config.h`; `target.c` supplies the timer/DMA resource table and
`config.c` supplies board defaults.

The map is based on the factory Betaflight 4.4.1 unified configuration and was
cross-checked against mainline ArduPilot's `OrqaH7QuadCore/hwdef.dat` and the
ORQA PX4 board port. Two corrections are deliberate:

- PA0/PA1 use TIM2, not TIM5.
- the second status LED uses PA10; PA11 is USB D-.

Hardware validation on each PCB revision is still required before flight.
