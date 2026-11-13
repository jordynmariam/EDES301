#!/bin/bash
# --------------------------------------------------------------------------
# Reaction Tug-of-War: Pin Configuration
# --------------------------------------------------------------------------
# Copyright 2026 Jordyn Mariam
# License: see tug_of_war.py (BSD 3-Clause)
# --------------------------------------------------------------------------
# Configure all PocketBeagle pins used by the Reaction Tug-of-War game.
# The potentiometer (AIN0, P1_19) needs no configuration.
# --------------------------------------------------------------------------

# 7-segment display (I2C1)
config-pin P2_09 i2c
config-pin P2_11 i2c

# Buttons: Player 1, Player 2, Start
config-pin P2_02 gpio
config-pin P2_04 gpio
config-pin P2_06 gpio

# Buzzer (PWM)
config-pin P2_01 pwm

# LED strip data (SPI0)
config-pin P1_08 spi
config-pin P1_12 spi
