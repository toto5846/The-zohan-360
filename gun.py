from gpiozero import OutputDevice, Button
from time import sleep

# Stepper driver pins
dir_pin = OutputDevice(20)
step_pin = OutputDevice(21)

# Button on GPIO 0
button = Button(0, pull_up=True)

# 90 degrees for 200 step motor
steps = 50

# Speed
delay = 0.001

def move(direction):

    # Set direction
    dir_pin.value = direction

    # Send step pulses
    for _ in range(steps):
        step_pin.on()
        sleep(delay)
        step_pin.off()
        sleep(delay)

while True:

    # Wait for button press
    button.wait_for_press()

    # Move 90 degrees
    move(True)

    # Tiny pause
    sleep(0.05)

    # Move back
    move(False)

    # Prevent double press
    sleep(0.1)
