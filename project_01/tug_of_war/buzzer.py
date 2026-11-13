# -*- coding: utf-8 -*-
"""
--------------------------------------------------------------------------
Reaction Tug-of-War: Buzzer
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
Software API:

  Buzzer(pin)
    - pin: Adafruit_BBIO PWM pin name, e.g. "P2_1" (no leading zero)

    start(frequency)            - Start a tone (Hz) and keep playing
    stop()                      - Stop the tone
    play(frequency, length)     - Play a tone for length seconds
    play_tune(notes)            - Play a list of (frequency, length) pairs;
                                  frequency 0 is a rest
    cleanup()                   - Stop the tone and release the PWM pin
--------------------------------------------------------------------------
"""
import time

import Adafruit_BBIO.PWM as PWM


# ------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------

DUTY_CYCLE = 50          # Percent; 50% gives the loudest square wave

# Tunes used by the game: lists of (frequency in Hz, length in seconds)
TUNE_START   = [(523, 0.08), (659, 0.08), (784, 0.12)]
TUNE_VICTORY = [(523, 0.12), (659, 0.12), (784, 0.12), (1047, 0.35)]
TUNE_LOSE    = [(392, 0.2), (330, 0.2), (262, 0.4)]
TUNE_BEST    = [(1047, 0.06), (0, 0.04), (1319, 0.1)]


# ------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------

class Buzzer():
    """ Buzzer driven by a PWM pin """

    def __init__(self, pin):
        """ Initialize variables """
        self.pin     = pin
        self.playing = False

    # End def

    def start(self, frequency):
        """ Start a tone and leave it playing """
        if self.playing:
            self.stop()
        PWM.start(self.pin, DUTY_CYCLE, frequency)
        self.playing = True

    # End def

    def stop(self):
        """ Stop the tone """
        if self.playing:
            PWM.stop(self.pin)
            self.playing = False

    # End def

    def play(self, frequency, length):
        """ Play a tone for length seconds """
        self.start(frequency)
        time.sleep(length)
        self.stop()

    # End def

    def play_tune(self, notes):
        """ Play a list of (frequency, length) pairs; frequency 0 = rest """
        for frequency, length in notes:
            if frequency > 0:
                self.play(frequency, length)
            else:
                time.sleep(length)
            time.sleep(0.02)

    # End def

    def cleanup(self):
        """ Stop the tone and release the PWM pin """
        self.stop()
        PWM.cleanup()

    # End def

# End class


# ------------------------------------------------------------------------
# Test
# ------------------------------------------------------------------------

if __name__ == '__main__':
    print("Buzzer test")
    buzzer = Buzzer("P2_1")

    print("Start tune")
    buzzer.play_tune(TUNE_START)
    time.sleep(0.5)

    print("Victory tune")
    buzzer.play_tune(TUNE_VICTORY)
    time.sleep(0.5)

    print("Lose tune")
    buzzer.play_tune(TUNE_LOSE)

    buzzer.cleanup()
    print("Done")
