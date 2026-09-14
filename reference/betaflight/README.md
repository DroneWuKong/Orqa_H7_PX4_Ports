# Betaflight ORQA H7 QuadCore reference

This directory preserves the Betaflight unified-target configuration used during
the ORQA H7 QuadCore PX4 port.

## Recovered artifact

- Original uploaded archive: `betaflight_4.4.1_STM32H743_ORQAH7QUADCORE.zip`
- Original archive contents:
  - `4.4.1/ORQAH7QuadCore.config`
  - `4.4.1/betaflight_4.4.1_STM32H743_ORQAH7QUADCORE.hex`
- Recovered file: `ORQAH7QuadCore.config`
- Recovered config SHA-256: `eaf239a5e973e963aebe71ee0d31ded9582149ce19f747e70ef837dbe2f2798a`

The archive contained no `config.h`; it used Betaflight's unified `.config` format
plus a compiled `.hex` image. The config text was recovered verbatim from the
recorded output of the original archive extraction performed on 2026-03-16. The original ZIP bytes were not
present in this repository, its Git history, or the retained file library, so an
archive checksum cannot be supplied.

## Important provenance notes

The recovered file's own header identifies:

```text
Betaflight / STM32H743 4.4.0 Apr 27 2021 / 18:42:02 (3ae7e91)
```

That differs from the archive/directory label `4.4.1`. Both values are retained
as historical evidence; this repository does not resolve the discrepancy.

The source text is intentionally unchanged, including apparent original tokens
such as `USE_CURRETN_SENSOR_ADC` and `baro_hardware = DSP310`. Do not silently
correct them in this evidence file.

## Scope and safety

This is a reference artifact, not a PX4 build input and not proof of a
flashable or flight-qualified Betaflight target. It does not enable any hardware,
motor, control, or flight authority.

Before using it with Betaflight:

1. Confirm the intended Betaflight source revision and target format.
2. Review every resource, timer, DMA, sensor, and serial assignment against the
   exact board revision and schematic.
3. Resolve the recorded version and token discrepancies in a separate derived
   file.
4. Validate in software first, then perform any bench work props-off.

The PX4 board definitions cross-reference this config with ArduPilot
`OrqaH7QuadCore/hwdef.dat`, the STM32H743VIH6 schematic, and ORQA's PX4 fork.
