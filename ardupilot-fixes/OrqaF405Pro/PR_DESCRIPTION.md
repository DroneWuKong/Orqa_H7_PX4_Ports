# PR: Fix OrqaF405Pro hwdef — duplicate IMU SPIDEV + README battery pins

## Summary

Two bugs in the OrqaF405Pro board definition:

### 1. Duplicate SPIDEV for IMU (hwdef.dat)

`imu1` and `imu2` were defined as separate SPIDEV entries pointing to the same SPI bus and CS pin:

```
SPIDEV imu1   SPI1 DEVID1 GYRO1_CS   MODE3   1*MHZ   8*MHZ
SPIDEV imu2   SPI1 DEVID1 GYRO1_CS   MODE3   1*MHZ   8*MHZ
```

This is a single-IMU board. Both driver probes (Invensense for MPU6000, Invensensev3 for ICM42688P) should reference the same SPIDEV `imu1`. Fixed by removing the duplicate `imu2` entry and updating the `IMU Invensensev3` line to use `SPI:imu1`.

### 2. Incorrect battery pin numbers (README.md)

The README documented wrong pin numbers for battery monitoring:

| Parameter | README (wrong) | hwdef.dat (correct) |
|-----------|---------------|-------------------|
| BATT_VOLT_PIN | 13 | 11 (PC1 = ADC1_CH11) |
| BATT_CURR_PIN | 12 | 13 (PC3 = ADC1_CH13) |

## Testing

- Verified pin numbers against hwdef.dat ADC defines
- Cross-referenced with ORQA official PX4 fork (`orqafpv/PX4-Autopilot`)
- No functional change to IMU behavior (both drivers still probe PA4/GYRO1_CS)

## Board

OrqaF405Pro (AP_HW_ORQAF405PRO, board ID 1155)
