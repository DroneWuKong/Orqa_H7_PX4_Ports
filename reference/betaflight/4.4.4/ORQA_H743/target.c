/*
 * ORQA H7 QuadCore timer/resource map.
 */

#include <stdint.h>

#include "platform.h"
#include "drivers/io.h"
#include "drivers/dma.h"
#include "drivers/timer.h"
#include "drivers/timer_def.h"

const timerHardware_t timerHardware[USABLE_TIMER_CHANNEL_COUNT] = {
    /* Eight motor outputs.  DMA options reproduce the factory mapping. */
    DEF_TIM(TIM4,  CH1, PD12, TIM_USE_MOTOR,  0, 6, 0), // M1
    DEF_TIM(TIM4,  CH2, PD13, TIM_USE_MOTOR,  0, 7, 0), // M2
    DEF_TIM(TIM2,  CH2, PA1,  TIM_USE_MOTOR,  0, 3, 0), // M3
    DEF_TIM(TIM2,  CH1, PA0,  TIM_USE_MOTOR,  0, 2, 0), // M4
    DEF_TIM(TIM5,  CH3, PA2,  TIM_USE_MOTOR,  0, 4, 0), // M5
    DEF_TIM(TIM5,  CH4, PA3,  TIM_USE_MOTOR,  0, 5, 0), // M6
    DEF_TIM(TIM3,  CH4, PB1,  TIM_USE_MOTOR,  0, 1, 0), // M7
    DEF_TIM(TIM3,  CH3, PB0,  TIM_USE_MOTOR,  0, 0, 0), // M8

    /* Auxiliary servo outputs. */
    DEF_TIM(TIM15, CH2, PE6,  TIM_USE_SERVO,  0, 0, 0), // S1
    DEF_TIM(TIM15, CH1, PE5,  TIM_USE_SERVO,  0, 0, 0), // S2

    /* PWM beeper. */
    DEF_TIM(TIM1,  CH1, PE9,  TIM_USE_BEEPER, 0, 0, 0),
};
