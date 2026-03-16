/****************************************************************************
 *
 *   Copyright (C) 2024 PX4 Development Team. All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions
 * are met:
 *
 * 1. Redistributions of source code must retain the above copyright
 *    notice, this list of conditions and the following disclaimer.
 * 2. Redistributions in binary form must reproduce the above copyright
 *    notice, this list of conditions and the following disclaimer in
 *    the documentation and/or other materials provided with the
 *    distribution.
 * 3. Neither the name PX4 nor the names of its contributors may be
 *    used to endorse or promote products derived from this software
 *    without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 * "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 * LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
 * FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
 * COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
 * INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
 * BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS
 * OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED
 * AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
 * LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
 * ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
 * POSSIBILITY OF SUCH DAMAGE.
 *
 ****************************************************************************/

/**
 * @file timer_config.cpp
 *
 * ORQA H7 Wingcore PWM output configuration
 *
 * Motor outputs (DSHOT-capable, bidirectional):
 *   PWM1: PD12 TIM4_CH1   (MOTOR 1)
 *   PWM2: PD13 TIM4_CH2   (MOTOR 2)
 *   PWM3: PA1  TIM2_CH2   (MOTOR 3)
 *   PWM4: PA0  TIM2_CH1   (MOTOR 4)
 *   PWM5: PA2  TIM5_CH3   (MOTOR 5)
 *   PWM6: PA3  TIM5_CH4   (MOTOR 6)
 *   PWM7: PB1  TIM3_CH4   (MOTOR 7)
 *   PWM8: PB0  TIM3_CH3   (MOTOR 8)
 *
 * Servo outputs (PWM only, no DMA):
 *   PWM9:  PE6  TIM15_CH2  (SERVO 1)
 *   PWM10: PE5  TIM15_CH1  (SERVO 2)
 */

#include <px4_arch/io_timer_hw_description.h>

constexpr io_timers_t io_timers[MAX_IO_TIMERS] = {
	initIOTimer(Timer::Timer4, DMA{DMA::Index1}),
	initIOTimer(Timer::Timer2, DMA{DMA::Index1}),
	initIOTimer(Timer::Timer5, DMA{DMA::Index1}),
	initIOTimer(Timer::Timer3, DMA{DMA::Index1}),
	initIOTimer(Timer::Timer15),
};

constexpr timer_io_channels_t timer_io_channels[MAX_TIMER_IO_CHANNELS] = {
	/* Motors - DMA-capable */
	initIOTimerChannel(io_timers, {Timer::Timer4, Timer::Channel1}, {GPIO::PortD, GPIO::Pin12}),  /* PWM1 - MOTOR 1 */
	initIOTimerChannel(io_timers, {Timer::Timer4, Timer::Channel2}, {GPIO::PortD, GPIO::Pin13}),  /* PWM2 - MOTOR 2 */
	initIOTimerChannel(io_timers, {Timer::Timer2, Timer::Channel2}, {GPIO::PortA, GPIO::Pin1}),   /* PWM3 - MOTOR 3 */
	initIOTimerChannel(io_timers, {Timer::Timer2, Timer::Channel1}, {GPIO::PortA, GPIO::Pin0}),   /* PWM4 - MOTOR 4 */
	initIOTimerChannel(io_timers, {Timer::Timer5, Timer::Channel3}, {GPIO::PortA, GPIO::Pin2}),   /* PWM5 - MOTOR 5 */
	initIOTimerChannel(io_timers, {Timer::Timer5, Timer::Channel4}, {GPIO::PortA, GPIO::Pin3}),   /* PWM6 - MOTOR 6 */
	initIOTimerChannel(io_timers, {Timer::Timer3, Timer::Channel4}, {GPIO::PortB, GPIO::Pin1}),   /* PWM7 - MOTOR 7 */
	initIOTimerChannel(io_timers, {Timer::Timer3, Timer::Channel3}, {GPIO::PortB, GPIO::Pin0}),   /* PWM8 - MOTOR 8 */
	/* Servos - no DMA */
	initIOTimerChannel(io_timers, {Timer::Timer15, Timer::Channel2}, {GPIO::PortE, GPIO::Pin6}),  /* PWM9  - SERVO 1 */
	initIOTimerChannel(io_timers, {Timer::Timer15, Timer::Channel1}, {GPIO::PortE, GPIO::Pin5}),  /* PWM10 - SERVO 2 */
};

constexpr io_timers_channel_mapping_t io_timers_channel_mapping =
	initIOTimerChannelMapping(io_timers, timer_io_channels);
