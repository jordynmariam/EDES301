import time
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.PWM as PWM

# Buzzer: three rising beeps
print("Buzzer test...")
for freq in (440, 660, 880):
    PWM.start("P2_1", 50, freq)
    time.sleep(0.3)
    PWM.stop("P2_1")
    time.sleep(0.1)

# Buttons + potentiometer: live readout, Ctrl-C to quit
buttons = {"P1": "P2_2", "P2": "P2_4", "Start": "P2_6"}
for pin in buttons.values():
    GPIO.setup(pin, GPIO.IN)
ADC.setup()

print("Press buttons and turn the knob (Ctrl-C to stop)")
try:
    while True:
        states = "  ".join(
            f"{name}:{'PRESSED' if GPIO.input(pin) == 0 else '-------'}"
            for name, pin in buttons.items())
        knob = int(ADC.read_raw("P1_19"))
        print(f"\r{states}   knob: {knob:4d}", end="")
        time.sleep(0.1)
except KeyboardInterrupt:
    PWM.cleanup()
    GPIO.cleanup()
    print("\nDone")