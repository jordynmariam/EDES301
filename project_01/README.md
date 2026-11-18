<h1>Reaction Tug-of-War</h1>

A two-player reaction game built on the PocketBeagle. After a random "GO" cue, whoever hits their button first pulls a light on an LED-strip "rope" one step toward their side. The first player to pull the rope all the way to their end wins. The 7-segment display shows each round's reaction time in milliseconds.

This project builds on the [Whac-a-Mole Game with PocketBeagle](https://www.hackster.io/beaglefriends-octavosystems/whac-a-mole-game-with-pocketbeagle-738a4c) by Erik Welsh and Cathy Wicks.

**Hackster.io page (hardware build, parts list, video):** [Reaction Tug-of-War on Hackster](LINK-TO-HACKSTER-PAGE)

---

## Software Overview

All game code is in the `tug_of_war/` folder.

| File | Description |
|---|---|
| `tug_of_war/tug_of_war.py` | Main program: game logic (mode select, rounds, false starts, rope position, victory) |
| `tug_of_war/player_button.py` | Timestamps each player's button press (GPIO edge detection) so the first press wins |
| `tug_of_war/buzzer.py` | Plays tones and tunes on the buzzer (PWM) |
| `tug_of_war/led_strip.py` | Drives the WS2812B LED strip over SPI |
| `tug_of_war/rope.py` | Turns the rope position into LED patterns (or a text rope in the terminal if no strip is connected) |
| `tug_of_war/stats.py` | Saves the best reaction time and win counts to `stats.json` |
| `tug_of_war/configure_pins.sh` | Sets up all PocketBeagle pins used by the project |
| `tug_of_war/run` | Runs the pin setup and starts the game (used for autoboot) |
| `tug_of_war/hw_test.py` | Hardware test for the buttons, potentiometer and buzzer |
| `../python/ht16k33/ht16k33.py` | 7-segment display (HT16K33) driver |

See `docs/` for the project proposal, block diagrams, and software flow diagram.

---

## Software Build Instructions

These instructions assume a PocketBeagle running the standard BeagleBoard.org Debian image, accessed through Cloud9.

1. **Copy the repository onto the PocketBeagle** so that it is located at:
   ```
   /var/lib/cloud9/EDES301
   ```
   (Either `git clone` the repository on a PocketBeagle with internet access, or drag the files into Cloud9.)

2. **Check that the required libraries are installed.** Adafruit_BBIO and i2c-tools come with the BeagleBoard Debian image. The display driver must be at `/var/lib/cloud9/EDES301/python/ht16k33/` (the `run` script adds it to `PYTHONPATH`). Install spidev if it is missing:
   ```bash
   sudo pip3 install spidev
   ```

3. **Make the scripts executable:**
   ```bash
   cd /var/lib/cloud9/EDES301/project_01/tug_of_war
   chmod 755 configure_pins.sh run
   ```

4. **Configure the pins:**
   ```bash
   ./configure_pins.sh
   ```

5. **Test the hardware (optional):**
   ```bash
   sudo python3 hw_test.py
   ```
   You should hear three beeps, see each button show PRESSED when held, and see the knob value change from about 0 to 4095.

   To test the LED strip by itself, check which SPI device the PocketBeagle has with `ls /dev/spidev*` (the code uses `spidev0.0`; change `SPI_BUS` / `SPI_DEVICE` in `tug_of_war.py` if yours differs), then run `sudo python3 led_strip.py`.

6. **Set up autoboot** so the game starts when the PocketBeagle powers on:
   ```bash
   mkdir -p /var/lib/cloud9/logs
   sudo crontab -e
   ```
   Add this line at the bottom, then save:
   ```
   @reboot sleep 30 && bash /var/lib/cloud9/EDES301/project_01/tug_of_war/run > /var/lib/cloud9/logs/cronlog 2>&1
   ```

### Pin Connections

| Component | PocketBeagle Pin |
|---|---|
| 7-segment display SCL / SDA | P2_09 / P2_11 (I2C1) |
| Player 1 button | P2_02 |
| Player 2 button | P2_04 |
| Start / mode button | P2_06 |
| Buzzer | P2_01 (PWM) |
| Potentiometer (wiper) | P1_19 (AIN0), powered from P1_18 (1.8 V) and P1_17 (analog GND) |
| LED strip data (through level shifter) | P1_12 (SPI0 MOSI) |
| LED strip power | P1_07 (5 V from USB) |

---

## Software Operation Instructions

### Starting the game

- **Automatically:** power on the PocketBeagle. After about 30 seconds, the game starts.
- **Manually:**
  ```bash
  cd /var/lib/cloud9/EDES301/project_01/tug_of_war
  sudo ./run
  ```

### How to play

1. The display shows the best reaction time. Press the **Start** button to begin:
   - **Short press (less than 2 seconds):** 2-player mode
   - **Hold (more than 2 seconds):** 1-player mode against the computer
2. Turn the **knob** to set the difficulty (how fast the computer reacts in 1-player mode).
3. Each round, the display shows `rdy` and the game waits a random 1 to 4 seconds.
4. When the buzzer beeps and the strip flashes (**GO!**), hit your button as fast as you can.
   - The faster player pulls the rope one step toward their side.
   - The winner's reaction time is shown in milliseconds.
   - **False start:** pressing before GO moves the rope one step toward your opponent.
5. The first player to pull the rope to their end wins. A victory animation and tune play, and the game returns to the start screen.

### Stopping the game

- Press **Ctrl-C** in the terminal if running manually. The display shows `----` and the LED strip turns off.
- If the game was started at boot, stop it with:
  ```bash
  ps -ef | grep tug_of_war
  sudo kill -9 <process id>
  ```
  To stop it from starting at boot, run `sudo crontab -e` and put `#` in front of the `@reboot` line.

---

## Author

Jordyn Mariam, EDES 301, Rice University, Fall 2026
