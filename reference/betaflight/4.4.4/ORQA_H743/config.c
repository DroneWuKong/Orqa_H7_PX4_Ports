/* Board defaults that cannot be expressed completely by target macros. */

#include <stdbool.h>
#include <stdint.h>

#include "platform.h"

#include "config_helper.h"
#include "drivers/pwm_output.h"
#include "io/serial.h"
#include "pg/motor.h"
#include "pg/piniobox.h"
#include "sensors/barometer.h"

void targetConfiguration(void)
{
    static targetSerialPortFunction_t serialPortFunctions[] = {
        { SERIAL_PORT_USART3, FUNCTION_RX_SERIAL },
        { SERIAL_PORT_USART7, FUNCTION_GPS },
        { SERIAL_PORT_USART8, FUNCTION_ESC_SENSOR },
    };

    targetSerialPortFunctionConfig(serialPortFunctions, ARRAYLEN(serialPortFunctions));

    /* The onboard DPS310 has SDO pulled high: 7-bit address 0x77. */
    barometerConfigMutable()->baro_hardware = BARO_DPS310;
    barometerConfigMutable()->baro_i2c_address = 0x77;

    motorConfigMutable()->dev.motorPwmProtocol = PWM_TYPE_DSHOT300;
    motorConfigMutable()->dev.useDshotTelemetry = true;

    /* BOXUSER1, used by the original firmware for the camera switch. */
    pinioBoxConfigMutable()->permanentId[0] = 43;
}
