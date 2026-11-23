# -*- coding: utf-8 -*-
"""
--------------------------------------------------------------------------
Reaction Tug-of-War: Hardware Test
--------------------------------------------------------------------------
License:
Copyright 2026 Jordyn Mariam

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
this list of conditions and the following disclaimer in the documentation
and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors
may be used to endorse or promote products derived from this software without
specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
--------------------------------------------------------------------------
Quick test of the wiring for the buzzer, buttons and potentiometer.

  - Plays three rising beeps on the buzzer (P2_01)
  - Then shows a live readout of the three buttons (P2_02, P2_04, P2_06)
    and the potentiometer (P1_19, 0-4095) until Ctrl-C

Run with:  ./configure_pins.sh  then  sudo python3 hw_test.py
--------------------------------------------------------------------------
"""
import time

import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.PWM as PWM


# ------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------

BUZZER_PIN = "P2_1"
POT_PIN    = "P1_19"
BUTTONS    = {"P1": "P2_2", "P2": "P2_4", "Start": "P2_6"}


# ------------------------------------------------------------------------
# Main script
# ------------------------------------------------------------------------

if __name__ == '__main__':
    # Buzzer: three rising beeps
    print("Buzzer test...")
    for freq in (440, 660, 880):
        PWM.start(BUZZER_PIN, 50, freq)
        time.sleep(0.3)
        PWM.stop(BUZZER_PIN)
        time.sleep(0.1)

    # Buttons + potentiometer: live readout
    for pin in BUTTONS.values():
        GPIO.setup(pin, GPIO.IN)
    ADC.setup()

    print("Press buttons and turn the knob (Ctrl-C to stop)")
    try:
        while True:
            states = "  ".join(
                "{0}:{1}".format(name, "PRESSED" if GPIO.input(pin) == 0 else "-------")
                for name, pin in BUTTONS.items())
            knob = int(ADC.read_raw(POT_PIN))
            print("\r{0}   knob: {1:4d}".format(states, knob), end="")
            time.sleep(0.1)
    except KeyboardInterrupt:
        PWM.cleanup()
        GPIO.cleanup()
        print("\nDone")
