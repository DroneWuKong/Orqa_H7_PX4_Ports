# Betaflight ORQA targets and reference material

This directory contains PCB-specific Betaflight targets for the standalone ORQA
H7 QuadCore and the ORQA DTK APB, plus the historical unified-target evidence
used during the original PX4 port.

## Available targets

| Board | Betaflight | Target files | Status |
| --- | --- | --- | --- |
| ORQA H7 QuadCore | 2026.6 | [config.h](2026.6/configs/ORQA/ORQA_H743/config.h), [build notes](2026.6/configs/ORQA/ORQA_H743/README.md) | Compiles and links on 2026.6.2 |
| ORQA DTK APB | 2026.6 | [config.h](2026.6/configs/ORQA/ORQA_APB/config.h), [build notes](2026.6/configs/ORQA/ORQA_APB/README.md) | Both sensor revisions compile and link on 2026.6.2 |
| ORQA H7 QuadCore | 4.4.4 | [source target and HEX](4.4.4/ORQA_H743/), [build notes](4.4.4/ORQA_H743/README.md) | Compiles and links on 4.4.4 |
| ORQA H7 QuadCore historical evidence | 4.4.1 archive label | [recovered unified target](4.4.1/ORQAH7QuadCore.config) | Preserved verbatim; see provenance notes below |

From a Betaflight `2026.6-maintenance` checkout, point
`BETAFLIGHT_CONFIG` at this repository's `reference/betaflight/2026.6`
directory:

```sh
make CONFIG=ORQA_H743 \
  BETAFLIGHT_CONFIG=/path/to/Orqa_H7_PX4_Ports/reference/betaflight/2026.6

make CONFIG=ORQA_APB \
  BETAFLIGHT_CONFIG=/path/to/Orqa_H7_PX4_Ports/reference/betaflight/2026.6
```

The APB command above targets the original MPU6000 + ICM42605 population. For
the later dual-ICM42688P APB revision, add:

```sh
EXTRA_FLAGS=-DORQA_APB_IMU_ICM42688P
```

The APB uses Betaflight's normal H743 internal-flash layout. Its factory
ArduPilot bootloader expects an application at `0x08060000`, so it cannot
directly install the normal Betaflight HEX. Read the APB build notes and use a
verified STM32 DFU/SWD recovery procedure.

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

The recovered 4.4.1 file is a reference artifact, not a PX4 build input. The
derived targets are software-build validated, but none are hardware- or
flight-qualified. Merely storing these files does not enable hardware, motor,
control, or flight authority.

Before using any target with Betaflight:

1. Confirm the intended Betaflight source revision and target format.
2. Review every resource, timer, DMA, sensor, and serial assignment against the
   exact board revision and schematic.
3. Keep any correction to the recovered artifact in a separate derived file.
4. Validate in software first, then perform any bench work props-off.

The mappings were cross-checked against the recovered configuration, ArduPilot
board definitions, the STM32H743VIH6 schematic, and ORQA's PX4 board ports. See
the per-target build notes for the applicable sources and remaining boundaries.
