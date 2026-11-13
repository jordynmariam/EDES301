# -*- coding: utf-8 -*-
"""
--------------------------------------------------------------------------
Reaction Tug-of-War: Rope
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

  Rope(strip=None, steps=5, num_leds=15)
    - strip:  An LEDStrip, or None to draw the rope in the terminal instead
    - steps:  How many steps from the center to either end (rounds to win)

    draw(position)          - Show the rope; position runs from -steps
                              (all the way to P1) to +steps (all the way to P2)
    go()                    - Flash the whole strip green for the GO cue
    flash(color, times)     - Blink the whole strip a color
    win_animation(player)   - Victory animation in the winner's color
    idle()                  - Rope at the center
    clear()                 - Turn the rope off

Rope layout:
  LED 0 is the Player 1 end; the last LED is the Player 2 end.
  P1's half is dim red, P2's half is dim blue, and the rope marker is
  bright yellow.
--------------------------------------------------------------------------
"""
import time


# ------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------

P1_COLOR     = (255, 0, 0)
P2_COLOR     = (0, 60, 255)
MARKER_COLOR = (255, 200, 0)
GO_COLOR     = (0, 255, 0)
OFF          = (0, 0, 0)
DIM          = 0.15            # Background halves at 15% of full color

TERMINAL_LEDS = 15


def _dim(color, amount=DIM):
    return tuple(int(c * amount) for c in color)


# ------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------

class Rope():
    """ Shows the tug-of-war rope on the LED strip (or the terminal) """

    def __init__(self, strip=None, steps=5, num_leds=TERMINAL_LEDS):
        """ Initialize variables """
        self.strip    = strip
        self.steps    = steps
        self.num_leds = strip.num_leds if strip else num_leds
        self.center   = (self.num_leds - 1) // 2

    # End def

    def _index(self, position):
        """ Convert a rope position into an LED index """
        position = max(-self.steps, min(self.steps, position))
        return self.center + round(position * self.center / self.steps)

    # End def

    def draw(self, position):
        """ Show the rope at the given position """
        marker = self._index(position)

        if self.strip:
            for i in range(self.num_leds):
                if i == marker:
                    color = MARKER_COLOR
                elif i < self.center:
                    color = _dim(P1_COLOR)
                elif i > self.center:
                    color = _dim(P2_COLOR)
                else:
                    color = _dim(MARKER_COLOR)
                self.strip.set_pixel(i, color)
            self.strip.show()
        else:
            cells = ["-"] * self.num_leds
            cells[self.center] = "|"
            cells[marker] = "O"
            print("ROPE   P1 [{0}] P2   (position {1:+d})".format("".join(cells), position))

    # End def

    def go(self):
        """ Light the whole strip green for the GO cue (does not wait) """
        if self.strip:
            self.strip.fill(GO_COLOR)
            self.strip.show()
        else:
            print("ROPE   *** GO! ***")

    # End def

    def flash(self, color, times=1, length=0.1):
        """ Blink the whole strip a color """
        if not self.strip:
            return
        for _ in range(times):
            self.strip.fill(color)
            self.strip.show()
            time.sleep(length)
            self.strip.fill(OFF)
            self.strip.show()
            time.sleep(length)

    # End def

    def win_animation(self, player):
        """ Victory animation in the winner's color """
        color = P1_COLOR if player == "P1" else P2_COLOR

        if not self.strip:
            print("ROPE   {0} WINS!".format(player))
            return

        # Fill from the winner's end, then blink
        order = range(self.num_leds) if player == "P1" else range(self.num_leds - 1, -1, -1)
        self.strip.fill(OFF)
        for i in order:
            self.strip.set_pixel(i, color)
            self.strip.show()
            time.sleep(0.04)
        self.flash(color, times=3, length=0.2)

    # End def

    def idle(self):
        """ Rope at the center """
        self.draw(0)

    # End def

    def clear(self):
        """ Turn the rope off """
        if self.strip:
            self.strip.clear()

    # End def

# End class


# ------------------------------------------------------------------------
# Test
# ------------------------------------------------------------------------

if __name__ == '__main__':
    print("Rope test (terminal only)")
    rope = Rope(strip=None, steps=5)
    for position in range(-5, 6):
        rope.draw(position)
    rope.win_animation("P2")
