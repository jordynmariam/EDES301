# -*- coding: utf-8 -*-
"""
--------------------------------------------------------------------------
Reaction Tug-of-War: Player Button
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

  PlayerButton(pin, name="", press_low=True, debounce_ms=50, use_edge=False)
    - pin:        Adafruit_BBIO pin name, e.g. "P2_2" (no leading zero)
    - name:       Label used by the game, e.g. "P1"
    - press_low:  True if the button reads 0 when pressed (pull-up wiring)
    - use_edge:   True to use GPIO edge detection instead of polling

    is_pressed()        - True while the button is held down
    arm()               - Clear any old press and start recording the next one
    disarm()            - Stop recording presses
    was_pressed()       - True if a press was recorded since arm()
    get_press_time()    - time.monotonic() timestamp of that press (or None)
    wait_for_press()    - Wait for a full press and release; returns how long
                          the button was held, in seconds
    cleanup()           - Stop edge detection / polling

Notes:
  * Each button has its own background thread that checks the pin every
    1 ms and records the time of a press the moment it sees it, so the game
    can compare two players fairly instead of checking the buttons one after
    another in a loop.
  * GPIO edge detection (use_edge=True) is also supported, but it did not
    report presses reliably on my PocketBeagle, so polling is the default.
--------------------------------------------------------------------------
"""
import time
import threading

import Adafruit_BBIO.GPIO as GPIO


# ------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------

POLL_PERIOD = 0.001      # Seconds between checks in polling mode
WAIT_PERIOD = 0.01       # Seconds between checks in wait_for_press()


# ------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------

class PlayerButton():
    """ Button that records the exact time it was pressed """

    def __init__(self, pin, name="", press_low=True, debounce_ms=50, use_edge=False):
        """ Initialize variables and set up the button pin """
        self.pin         = pin
        self.name        = name
        self.press_low   = press_low
        self.debounce_ms = debounce_ms
        self.use_edge    = use_edge
        self.mode        = None

        self._lock       = threading.Lock()
        self._armed      = False
        self._press_time = None
        self._running    = True
        self._thread     = None

        self._setup()

    # End def

    def _setup(self):
        """ Configure the pin and start watching for presses """
        GPIO.setup(self.pin, GPIO.IN)

        if self.use_edge:
            edge = GPIO.FALLING if self.press_low else GPIO.RISING
            try:
                GPIO.add_event_detect(self.pin, edge,
                                      callback=self._on_press,
                                      bouncetime=self.debounce_ms)
                self.mode = "edge"
                return
            except Exception as error:
                print("{0}: edge detection unavailable ({1}); using polling".format(self.name, error))

        self.mode    = "polling"
        self._thread = threading.Thread(target=self._poll, daemon=True)
        self._thread.start()

    # End def

    def _on_press(self, channel=None):
        """ Record the time of the first press after arm() """
        now = time.monotonic()
        with self._lock:
            if self._armed and (self._press_time is None):
                self._press_time = now

    # End def

    def _poll(self):
        """ Fallback: watch the pin in a background thread """
        last = self.is_pressed()
        while self._running:
            current = self.is_pressed()
            if current and not last:
                self._on_press()
            last = current
            time.sleep(POLL_PERIOD)

    # End def

    def is_pressed(self):
        """ Return True while the button is held down """
        value = GPIO.input(self.pin)
        if self.press_low:
            return value == 0
        return value == 1

    # End def

    def arm(self):
        """ Clear any old press and start recording the next one """
        with self._lock:
            self._press_time = None
            self._armed      = True

    # End def

    def disarm(self):
        """ Stop recording presses """
        with self._lock:
            self._armed = False

    # End def

    def was_pressed(self):
        """ Return True if a press was recorded since arm() """
        with self._lock:
            return self._press_time is not None

    # End def

    def get_press_time(self):
        """ Return the time.monotonic() time of the recorded press, or None """
        with self._lock:
            return self._press_time

    # End def

    def wait_for_press(self):
        """ Wait for a press and release; return how long it was held (s) """
        # Wait for any current press to end first
        while self.is_pressed():
            time.sleep(WAIT_PERIOD)

        while not self.is_pressed():
            time.sleep(WAIT_PERIOD)

        start = time.monotonic()

        while self.is_pressed():
            time.sleep(WAIT_PERIOD)

        return time.monotonic() - start

    # End def

    def cleanup(self):
        """ Stop edge detection / polling """
        self._running = False
        if self.mode == "edge":
            try:
                GPIO.remove_event_detect(self.pin)
            except Exception:
                pass

    # End def

# End class


# ------------------------------------------------------------------------
# Test
# ------------------------------------------------------------------------

if __name__ == '__main__':
    print("PlayerButton test: two players press after GO (Ctrl-C to quit)")

    p1 = PlayerButton("P2_2", "P1")
    p2 = PlayerButton("P2_4", "P2")
    print("Mode: {0}".format(p1.mode))

    try:
        while True:
            input("\nPress Enter, then both players press after 'GO!'")
            time.sleep(1)
            p1.arm()
            p2.arm()
            t0 = time.monotonic()
            print("GO!")
            time.sleep(2)

            for p in (p1, p2):
                if p.was_pressed():
                    print("{0}: {1:.0f} ms".format(p.name, (p.get_press_time() - t0) * 1000))
                else:
                    print("{0}: no press".format(p.name))
    except KeyboardInterrupt:
        p1.cleanup()
        p2.cleanup()
        GPIO.cleanup()
        print("\nDone")
