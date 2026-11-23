# -*- coding: utf-8 -*-
"""
--------------------------------------------------------------------------
Reaction Tug-of-War: Main Program
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
Main program for the Reaction Tug-of-War game.

How to play:
  - Press Start: short press = 2-player, hold > 2 s = 1-player vs. CPU
  - The knob sets how fast the CPU reacts (1-player mode)
  - Display shows "rdy", then after a random 1-4 s wait: GO! (beep + flash)
  - First button press pulls the rope one step toward that player;
    the reaction time (ms) is shown on the display
  - Pressing before GO is a false start ("FoUL"): the rope moves toward
    the other player
  - First player to pull the rope to their end wins

Hardware (see configure_pins.sh):
  - HT16K33 7-segment display    I2C1 (P2_09 SCL / P2_11 SDA)
  - Player 1 button              P2_02
  - Player 2 button              P2_04
  - Start / mode button          P2_06
  - Buzzer                       P2_01 (PWM)
  - Potentiometer                P1_19 (AIN0)
  - WS2812B LED strip            P1_12 (SPI0 MOSI) through a level shifter

Run with:  sudo ./run
  (or: sudo PYTHONPATH=/var/lib/cloud9/EDES301/python/ht16k33 python3 tug_of_war.py)

If the LED strip is not connected, the game still runs and draws the rope
in the terminal instead.
--------------------------------------------------------------------------
"""
import os
import random
import time

import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.GPIO as GPIO

import ht16k33
from player_button import PlayerButton
from buzzer import Buzzer, TUNE_START, TUNE_VICTORY, TUNE_LOSE, TUNE_BEST
from rope import Rope
from stats import StatsStore


# ------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------

# Pins (Adafruit_BBIO names: no leading zero)
P1_PIN       = "P2_2"
P2_PIN       = "P2_4"
START_PIN    = "P2_6"
BUZZER_PIN   = "P2_1"
POT_PIN      = "P1_19"

# Display
I2C_BUS      = 1
I2C_ADDRESS  = 0x70

# LED strip
NUM_LEDS     = 15
SPI_BUS      = 0
SPI_DEVICE   = 0
BRIGHTNESS   = 0.2         # Keeps the strip's current draw low

# Game settings
STEPS            = 5       # Rounds needed to pull the rope to one end
HOLD_TIME        = 2.0     # Hold Start longer than this for 1-player mode
MIN_WAIT         = 1.0     # Random wait before GO (seconds)
MAX_WAIT         = 4.0
ROUND_TIMEOUT    = 2.0     # Nobody scores if nobody presses within this time
ROUND_PAUSE      = 1.5     # Time to show the result before the next round
BEEP_LENGTH      = 0.15
GO_FREQ          = 1047
FOUL_FREQ        = 196
CPU_SLOW_MS      = 450     # CPU reaction time with the knob all the way down
CPU_FAST_MS      = 200     # CPU reaction time with the knob all the way up
CPU_JITTER_MS    = 30

TWO_PLAYER   = "2P"
ONE_PLAYER   = "1P"

STATS_FILE   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "stats.json")


# ------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------

class TugOfWarGame():
    """ Reaction Tug-of-War game """

    def __init__(self):
        """ Initialize variables and set up hardware """
        self.display  = None
        self.p1       = None
        self.p2       = None
        self.start    = None
        self.buzzer   = None
        self.strip    = None
        self.rope     = None
        self.stats    = None
        self.mode     = TWO_PLAYER
        self.position = 0

        self._setup()

    # End def

    def _setup(self):
        """ Set up all hardware components """
        self.display = ht16k33.HT16K33(I2C_BUS, I2C_ADDRESS)
        self.display.text("----")

        self.p1    = PlayerButton(P1_PIN, "P1")
        self.p2    = PlayerButton(P2_PIN, "P2")
        self.start = PlayerButton(START_PIN, "Start")

        ADC.setup()

        self.buzzer = Buzzer(BUZZER_PIN)

        # LED strip is optional: fall back to the terminal if it is not there
        try:
            from led_strip import LEDStrip
            self.strip = LEDStrip(NUM_LEDS, SPI_BUS, SPI_DEVICE, BRIGHTNESS)
        except Exception as error:
            print("LED strip not available ({0}); drawing rope in terminal".format(error))
            self.strip = None
        self.rope = Rope(self.strip, STEPS)

        self.stats = StatsStore(STATS_FILE)
        self.stats.load()

    # End def

    # --------------------------------------------------------------------
    # Helpers
    # --------------------------------------------------------------------

    def show_best(self):
        """ Show the best reaction time, or ---- if there is none """
        best = self.stats.get_best()
        if best is None:
            self.display.text("----")
        else:
            self.display.update(min(best, 9999))

    # End def

    def read_difficulty(self):
        """ Knob position from 0.0 (easy) to 1.0 (hard) """
        return ADC.read_raw(POT_PIN) / 4095.0

    # End def

    def cpu_reaction_ms(self):
        """ CPU reaction time based on the difficulty knob """
        difficulty = self.read_difficulty()
        base = CPU_SLOW_MS - difficulty * (CPU_SLOW_MS - CPU_FAST_MS)
        return base + random.uniform(-CPU_JITTER_MS, CPU_JITTER_MS)

    # End def

    def opponent_name(self):
        return "CPU" if self.mode == ONE_PLAYER else "P2"

    # End def

    # --------------------------------------------------------------------
    # Game states
    # --------------------------------------------------------------------

    def select_mode(self):
        """ Idle: show best time, wait for Start, pick 1P or 2P """
        self.show_best()
        self.rope.idle()
        print("\nPress Start (short = 2-player, hold > {0:.0f} s = 1-player)".format(HOLD_TIME))

        duration = self.start.wait_for_press()

        if duration > HOLD_TIME:
            self.mode = ONE_PLAYER
            self.display.text("1P")
        else:
            self.mode = TWO_PLAYER
            self.display.text("2P")

        print("Mode: {0}".format(self.mode))
        self.buzzer.play_tune(TUNE_START)
        time.sleep(1)

    # End def

    def new_game(self):
        """ Put the rope back in the center """
        self.position = 0
        self.rope.draw(self.position)

    # End def

    def play_round(self):
        """ One round: ready, random wait, GO, first press wins """
        players = [self.p1] if self.mode == ONE_PLAYER else [self.p1, self.p2]

        # Ready: random wait, watching for false starts
        self.display.text("rdy")
        self.rope.draw(self.position)
        for p in players:
            p.arm()

        end_wait = time.monotonic() + random.uniform(MIN_WAIT, MAX_WAIT)
        while time.monotonic() < end_wait:
            for p in players:
                if p.was_pressed():
                    self.false_start(p.name, players)
                    return
            time.sleep(0.005)

        # GO!
        for p in players:
            p.arm()
        t0 = time.monotonic()
        self.buzzer.start(GO_FREQ)
        self.rope.go()
        self.display.text("go")
        beep_off = t0 + BEEP_LENGTH

        cpu_time = None
        if self.mode == ONE_PLAYER:
            cpu_time = t0 + self.cpu_reaction_ms() / 1000.0

        # Wait for the first press (or CPU, or timeout)
        times = {}
        while True:
            now = time.monotonic()
            if self.buzzer.playing and now >= beep_off:
                self.buzzer.stop()

            times = {p.name: p.get_press_time() for p in players if p.was_pressed()}
            if (cpu_time is not None) and (now >= cpu_time):
                times["CPU"] = cpu_time

            if times or (now - t0 > ROUND_TIMEOUT):
                break
            time.sleep(0.001)

        # Short grace period so a near-simultaneous press is still compared
        time.sleep(0.02)
        for p in players:
            if p.was_pressed():
                times[p.name] = p.get_press_time()
            p.disarm()
        self.buzzer.stop()

        if not times:
            print("No press: nobody scores")
            self.display.text("----")
            self.rope.draw(self.position)
            time.sleep(ROUND_PAUSE)
            return

        # Earliest press wins the round
        winner = min(times, key=times.get)
        ms = int(round((times[winner] - t0) * 1000))

        if winner == "P1":
            self.position -= 1
        else:
            self.position += 1

        new_best = self.stats.record(winner, ms)

        print("{0} wins the round: {1} ms".format(winner, ms))
        self.display.update(min(ms, 9999))
        self.rope.draw(self.position)

        if new_best:
            print("New best reaction time!")
            self.buzzer.play_tune(TUNE_BEST)

        time.sleep(ROUND_PAUSE)

    # End def

    def false_start(self, player_name, players):
        """ Pressed before GO: rope moves toward the other player """
        for p in players:
            p.disarm()

        print("False start by {0}!".format(player_name))
        self.display.text("FoUL")
        self.buzzer.play(FOUL_FREQ, 0.4)

        if player_name == "P1":
            self.position += 1
        else:
            self.position -= 1

        self.rope.draw(self.position)
        time.sleep(ROUND_PAUSE)

    # End def

    def check_rope(self):
        """ Return the winner's name if the rope reached an end, else None """
        if self.position <= -STEPS:
            return "P1"
        if self.position >= STEPS:
            return self.opponent_name()
        return None

    # End def

    def victory(self, winner):
        """ Show the winner, play a tune, save stats """
        print("{0} wins the game!".format(winner))
        self.display.text("cpu" if winner == "CPU" else winner)

        self.stats.record_win(winner)
        self.stats.save()

        self.rope.win_animation("P1" if winner == "P1" else "P2")
        self.buzzer.play_tune(TUNE_LOSE if winner == "CPU" else TUNE_VICTORY)
        time.sleep(2)

    # End def

    # --------------------------------------------------------------------
    # Main loop
    # --------------------------------------------------------------------

    def run(self):
        """ Main program loop """
        while True:
            self.select_mode()
            self.new_game()

            winner = None
            while winner is None:
                self.play_round()
                winner = self.check_rope()

            self.victory(winner)

    # End def

    def cleanup(self):
        """ Leave the hardware in a known state """
        print("\nCleaning up")
        if self.display:
            self.display.text("----")
        if self.strip:
            self.strip.cleanup()
        if self.buzzer:
            self.buzzer.cleanup()
        for button in (self.p1, self.p2, self.start):
            if button:
                button.cleanup()
        if self.stats:
            self.stats.save()
        GPIO.cleanup()

    # End def

# End class


# ------------------------------------------------------------------------
# Main script
# ------------------------------------------------------------------------

if __name__ == '__main__':
    print("Reaction Tug-of-War")

    game = TugOfWarGame()

    try:
        game.run()
    except KeyboardInterrupt:
        pass
    finally:
        game.cleanup()

    print("Program complete")
