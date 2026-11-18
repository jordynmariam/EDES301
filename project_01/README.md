<h1>Reaction Tug-of-War</h1>

This is the code for my EDES 301 Project 1, a two-player reaction game on the PocketBeagle. After a random wait the buzzer beeps, and whoever presses their button first pulls the LED "rope" one step toward their side. First one to pull it all the way wins. The 7-segment display shows your reaction time in ms.

It's based on the [Whac-a-Mole Game with PocketBeagle](https://www.hackster.io/beaglefriends-octavosystems/whac-a-mole-game-with-pocketbeagle-738a4c) project.

The wiring, parts list, and video are on my Hackster page: [LINK-TO-HACKSTER-PAGE]

## Files

All the game code is in `project_01/tug_of_war/`:

- `tug_of_war.py` - main program with the game logic
- `player_button.py` - button class that records when each button was pressed, so it can tell who was faster
- `buzzer.py` - plays the beeps and tunes
- `led_strip.py` - controls the WS2812B LED strip using SPI
- `rope.py` - draws the rope on the LED strip (or prints it in the terminal if the strip isn't connected)
- `stats.py` - saves the best reaction time and win counts to `stats.json`
- `configure_pins.sh` - sets up the pins
- `run` - runs `configure_pins.sh` and then starts the game
- `hw_test.py` - quick test for the buttons, knob, and buzzer

The game also uses the HT16K33 display driver from class, which is in `python/ht16k33/`.

My proposal and the block/software diagrams are in `project_01/docs/`.

## Setup

This assumes the normal BeagleBoard Debian image on the PocketBeagle and that you're using Cloud9.

1. Copy this repo onto the PocketBeagle at `/var/lib/cloud9/EDES301`. The display driver needs to end up at `/var/lib/cloud9/EDES301/python/ht16k33/` because the `run` script looks for it there.

2. Adafruit_BBIO is already installed on the BeagleBoard image. If `spidev` isn't installed, install it:
   ```
   sudo pip3 install spidev
   ```

3. Make the scripts executable:
   ```
   cd /var/lib/cloud9/EDES301/project_01/tug_of_war
   chmod 755 configure_pins.sh run
   ```

4. (Optional) Test the hardware:
   ```
   ./configure_pins.sh
   sudo python3 hw_test.py
   ```
   It should beep three times, then show each button as PRESSED when you hold it and the knob value (0 to 4095) when you turn it.

   To test just the LED strip, run `sudo python3 led_strip.py`. The code uses `/dev/spidev0.0`. If `ls /dev/spidev*` shows something different on your board, change `SPI_BUS` and `SPI_DEVICE` at the top of `tug_of_war.py`.

5. To make the game start on boot, make a logs folder and edit the crontab:
   ```
   mkdir -p /var/lib/cloud9/logs
   sudo crontab -e
   ```
   and add this line at the bottom:
   ```
   @reboot sleep 30 && bash /var/lib/cloud9/EDES301/project_01/tug_of_war/run > /var/lib/cloud9/logs/cronlog 2>&1
   ```
   If it doesn't start after a reboot, check `/var/lib/cloud9/logs/cronlog` for errors.

The pins the code uses are listed at the top of `tug_of_war.py` and in `configure_pins.sh`. Note that Adafruit_BBIO wants pin names without the leading zero (`"P2_1"`, not `"P2_01"`).

## Running it

If autoboot is set up, just plug in the PocketBeagle and wait about 30 seconds. To run it by hand:
```
cd /var/lib/cloud9/EDES301/project_01/tug_of_war
sudo ./run
```

How to play:

1. The display shows the best time so far. Press Start. A short press is 2-player, and holding it for more than 2 seconds is 1-player against the computer.
2. In 1-player mode the knob sets how fast the computer is.
3. The display says `rdy` and waits 1 to 4 seconds.
4. When it beeps and says `go`, press your button. Whoever is faster moves the rope one step toward their side, and their time shows on the display.
5. If you press before the beep it says `FoUL` and the rope moves toward the other player.
6. First to get the rope 5 steps to their side wins.

To stop it, press Ctrl-C (the display goes to `----` and the strip turns off). If it was started on boot, find it with `ps -ef | grep tug_of_war` and stop it with `sudo kill -9 <pid>`. To turn off autoboot, put a `#` in front of the line in `sudo crontab -e`.

Jordyn Mariam, Fall 2026
