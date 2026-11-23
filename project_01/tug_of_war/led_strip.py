# -*- coding: utf-8 -*-
"""
--------------------------------------------------------------------------
Reaction Tug-of-War: LED Strip (WS2812B over SPI)
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

  LEDStrip(num_leds=15, bus=0, device=0, brightness=0.2)
    - num_leds:   Number of LEDs on the strip
    - bus/device: SPI device to use (/dev/spidev<bus>.<device>)
    - brightness: 0.0 - 1.0; scales every color to limit current draw

    set_pixel(index, color)     - Set one LED; color is (red, green, blue), 0-255
    fill(color)                 - Set every LED to one color
    clear()                     - Turn every LED off (and show it)
    set_brightness(brightness)  - Change the brightness scale
    show()                      - Send the colors to the strip
    cleanup()                   - Turn the strip off and close SPI

How it works:
  WS2812B LEDs read data as pulses with very precise timing, which Python
  cannot produce by toggling a GPIO pin. Instead, the SPI hardware sends
  bits at a steady 3.2 MHz, and each WS2812B data bit is encoded as four
  SPI bits:
      WS2812B "1"  ->  1110   (long high pulse)
      WS2812B "0"  ->  1000   (short high pulse)
  Only the SPI MOSI pin (P1_12) is used. Its 3.3 V signal goes through the
  level shifter to the strip's 5 V DIN input.

  If your PocketBeagle lists a different SPI device (check with
  "ls /dev/spidev*"), change SPI_BUS / SPI_DEVICE in tug_of_war.py.

  Uses the spidev Python library if it is installed. If not, it writes to
  /dev/spidevX.Y directly using Linux SPI ioctls, so no extra install is
  needed.
--------------------------------------------------------------------------
"""
import fcntl
import os
import struct
import time

try:
    import spidev                    # Preferred: the spidev library
except ImportError:
    spidev = None                    # Fallback: talk to /dev/spidev directly


# ------------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------------

SPI_SPEED_HZ   = 3200000       # 4 SPI bits per WS2812B bit = 800 kHz data
RESET_BYTES    = 120           # ~300 us of low signal to latch the colors
LEAD_BYTES     = 2             # Low bytes before the data

OFF            = (0, 0, 0)

# Linux SPI ioctl numbers (from linux/spi/spidev.h), used when the spidev
# library is not installed
SPI_IOC_WR_MODE         = 0x40016B01
SPI_IOC_WR_MAX_SPEED_HZ = 0x40046B04


class _SimpleSpi():
    """ Minimal write-only SPI device using /dev/spidevX.Y directly """

    def __init__(self, bus, device, speed_hz):
        self.fd = os.open("/dev/spidev{0}.{1}".format(bus, device), os.O_RDWR)
        fcntl.ioctl(self.fd, SPI_IOC_WR_MODE, struct.pack("B", 0))
        fcntl.ioctl(self.fd, SPI_IOC_WR_MAX_SPEED_HZ, struct.pack("I", speed_hz))

    def writebytes2(self, data):
        os.write(self.fd, bytes(data))

    def close(self):
        os.close(self.fd)


def _build_lookup():
    """ Precompute the 4 SPI bytes for every possible color byte """
    table = []
    for value in range(256):
        encoded = 0
        for bit in range(7, -1, -1):
            encoded = (encoded << 4) | (0b1110 if (value >> bit) & 1 else 0b1000)
        table.append(encoded.to_bytes(4, "big"))
    return table

LOOKUP = _build_lookup()


# ------------------------------------------------------------------------
# Classes
# ------------------------------------------------------------------------

class LEDStrip():
    """ WS2812B addressable LED strip driven over SPI """

    def __init__(self, num_leds=15, bus=0, device=0, brightness=0.2):
        """ Initialize variables and open the SPI device """
        self.num_leds   = num_leds
        self.brightness = brightness
        self.pixels     = [OFF] * num_leds

        if spidev is not None:
            self.spi = spidev.SpiDev()
            self.spi.open(bus, device)
            self.spi.max_speed_hz = SPI_SPEED_HZ
            self.spi.mode         = 0
        else:
            self.spi = _SimpleSpi(bus, device, SPI_SPEED_HZ)

        self.clear()

    # End def

    def set_pixel(self, index, color):
        """ Set one LED to a (red, green, blue) color """
        if 0 <= index < self.num_leds:
            self.pixels[index] = color

    # End def

    def fill(self, color):
        """ Set every LED to one color """
        self.pixels = [color] * self.num_leds

    # End def

    def clear(self):
        """ Turn every LED off """
        self.fill(OFF)
        self.show()

    # End def

    def set_brightness(self, brightness):
        """ Set brightness from 0.0 to 1.0 """
        self.brightness = max(0.0, min(1.0, brightness))

    # End def

    def _encode(self):
        """ Convert the pixel colors into SPI bytes """
        data = bytearray(LEAD_BYTES)
        for red, green, blue in self.pixels:
            # WS2812B expects green, red, blue order
            for value in (green, red, blue):
                scaled = int(max(0, min(255, value)) * self.brightness)
                data += LOOKUP[scaled]
        data += bytearray(RESET_BYTES)
        return data

    # End def

    def show(self):
        """ Send the current colors to the strip """
        data = self._encode()
        if hasattr(self.spi, "writebytes2"):
            self.spi.writebytes2(data)
        else:
            self.spi.xfer2(list(data))

    # End def

    def cleanup(self):
        """ Turn the strip off and close SPI """
        try:
            self.clear()
        finally:
            self.spi.close()

    # End def

# End class


# ------------------------------------------------------------------------
# Test
# ------------------------------------------------------------------------

if __name__ == '__main__':
    print("LED strip test")
    strip = LEDStrip(num_leds=15, bus=0, device=0, brightness=0.2)

    try:
        print("One LED at a time")
        for i in range(strip.num_leds):
            strip.fill(OFF)
            strip.set_pixel(i, (255, 0, 0))
            strip.show()
            time.sleep(0.1)

        for name, color in (("Red", (255, 0, 0)), ("Green", (0, 255, 0)), ("Blue", (0, 0, 255))):
            print(name)
            strip.fill(color)
            strip.show()
            time.sleep(1)
    except KeyboardInterrupt:
        pass

    strip.cleanup()
    print("Done")
