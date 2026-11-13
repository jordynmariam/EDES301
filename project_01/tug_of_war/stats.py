# -*- coding: utf-8 -*-
"""
--------------------------------------------------------------------------
Reaction Tug-of-War: Stats
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

  StatsStore(filename)
    - filename: JSON file to keep the stats in

    load()                  - Read the stats file (starts fresh if missing)
    save()                  - Write the stats file
    record(player, ms)      - Record a round won by player in ms; returns True
                              if it is a new best human reaction time
    record_win(player)      - Record a game won by player ("P1", "P2", "CPU")
    get_best()              - Best human reaction time in ms, or None

Stats are saved on the microSD card, so they survive reboots.
--------------------------------------------------------------------------
"""
import json
import os


# ------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------

class StatsStore():
    """ Saves best reaction time and win counts to a JSON file """

    def __init__(self, filename):
        """ Initialize variables """
        self.filename = filename
        self.data     = self._empty()

    # End def

    def _empty(self):
        return {"best_ms": None,
                "rounds": 0,
                "wins": {"P1": 0, "P2": 0, "CPU": 0}}

    # End def

    def load(self):
        """ Read the stats file; start fresh if it is missing or damaged """
        try:
            with open(self.filename, "r") as f:
                loaded = json.load(f)
            self.data = self._empty()
            self.data.update({k: loaded[k] for k in ("best_ms", "rounds") if k in loaded})
            self.data["wins"].update(loaded.get("wins", {}))
        except (OSError, ValueError):
            self.data = self._empty()

    # End def

    def save(self):
        """ Write the stats file (via a temporary file so it is never half-written) """
        temp = self.filename + ".tmp"
        try:
            with open(temp, "w") as f:
                json.dump(self.data, f, indent=2)
            os.replace(temp, self.filename)
        except OSError as error:
            print("Could not save stats: {0}".format(error))

    # End def

    def record(self, player, ms):
        """ Record a round; return True if it is a new best human time """
        self.data["rounds"] += 1
        if player == "CPU":
            return False
        best = self.data["best_ms"]
        if (best is None) or (ms < best):
            self.data["best_ms"] = ms
            return True
        return False

    # End def

    def record_win(self, player):
        """ Record a game won by player """
        self.data["wins"][player] = self.data["wins"].get(player, 0) + 1

    # End def

    def get_best(self):
        """ Best human reaction time in ms, or None """
        return self.data["best_ms"]

    # End def

# End class


# ------------------------------------------------------------------------
# Test
# ------------------------------------------------------------------------

if __name__ == '__main__':
    stats = StatsStore("stats_test.json")
    stats.load()
    print("Before: {0}".format(stats.data))
    print("New best? {0}".format(stats.record("P1", 250)))
    stats.record_win("P1")
    stats.save()
    print("After:  {0}".format(stats.data))
