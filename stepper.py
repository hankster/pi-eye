#! /usr/bin/env python

import os
import sys
import select
import time
import math
import getopt
import RPi.GPIO as GPIO

# Debug flag
debug = False

def Usage():
    print('Usage: stepper.py -d -h -v --debug --help --version degrees timing-in-milliseconds')

# Stepper motor operation -- 28BYJ48 5V DC motor
# 32 teeth (poles) per 360 degrees = 11.25 degrees per full step
# Using half-steps then 5.625 degrees per half-step
# Gear ratio = 3.5555 (32/9), 2.000 (22/11), 2.888 (26/9), 3.100 (31/10)
# Final gear ratio = 3.555 * 2.000 * 2.888 * 3.100 = 63.683950617
# One rotation of main shaft = 63.683950617 turns of rotor shaft
# But 63.683950617 turns of rotor shaft requires 63.683950617 * 64 steps = 4075.7728395 steps
# 0.0883268 degrees per step

# Stepper Motor Parameters
pi = 3.14159265358979323846
halfStep = 5.625
stepsRotor = 360.0/5.625
gearRatio = 63.683950617
stepsMain = gearRatio * stepsRotor
stepDegree = 360.0/stepsMain
lastStep = 0
degreesRotated = 0.0

# Default timing for each step
timing = 10.0

# Define GPIO signals to use
# Physical pins 31, 33, 35, 37
# GPIO06, GPIO13, GPIO19, GPIO26
gpioPins = [6, 13, 19, 26]

# Define half-step sequence
# as shown in manufacturers datasheet
seq = [[1,0,0,0],
       [1,1,0,0],
       [0,1,0,0],
       [0,1,1,0],
       [0,0,1,0],
       [0,0,1,1],
       [0,0,0,1],
       [1,0,0,1]]

# Step the motor. Degrees (positive or negative), time in milliseconds for each, energized state
def stepper(degrees, stepTime, stepLock) :

    global lastStep
    global stepDegree
    global degreesRotated
    
    # Use BCM GPIO references
    # instead of physical pin numbers
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    
    # Set all pins as output
    for pin in gpioPins:
        if debug:
            print('GPIO setup for pin %d' % pin)
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin, False)
      
    if degrees > 0.0 :
        direction = 1
    else:
        direction = -1

    # The amount of rotation may be slightly less than requested. Steps are integral    
    stepsNeeded = abs(int(degrees/stepDegree))
    stepCount = len(seq)
    
    # Start main loop

    # Variable for counting amount rotated in each step
    rotation = 0.0
    while stepsNeeded > 0 :

        lastStep = lastStep + direction
        if lastStep > len(seq) - 1 :
            lastStep = 0
        if lastStep < 0 :
            lastStep = len(seq) - 1
            
        for i in range(4):
            pin = gpioPins[i]
            if seq[lastStep][i]!=0 :
                if debug:
                    print('Step %d: Enable GPIO %i' % (lastStep, pin))
                GPIO.output(pin, True)
            else:
                if debug:
                    print ('Step %d: Disable GPIO %i' % (lastStep, pin))
                GPIO.output(pin, False)
                

        rotation = rotation + float(direction) * stepDegree
        if debug:
            print('Degrees rotated %4.3f' % rotation)
        time.sleep(stepTime/1000.0)
        stepsNeeded = stepsNeeded - 1

    # De-energize all output pins. Leave motor energized to lock-in the step.
    if not stepLock :
        for pin in gpioPins:
            GPIO.output(pin, False)
    return rotation

# Start of main program
def main(degrees, timing):

    global degreesRotated

    rotation = stepper(degrees, timing, False)
    degreesRotated = degreesRotated + rotation
    print('Degrees rotated: %4.3f' % degreesRotated)
    sys.exit(0)
    
if __name__ == "__main__":

    # This code corrects getopt's handling of negative numbers as arguments
    # Look for the first negative number (if any)
    for i,arg in enumerate(sys.argv[1:]):
        # stop if a non-argument is detected
        if arg[0] != "-":
            break
        # if a valid number is found insert a "--" string before it which
        # explicitly flags to getopt the end of options
        try:
            f = float(arg)
            sys.argv.insert(i+1,"--")
            break;
        except ValueError:
            pass
        
    try:
        options, args = getopt.getopt(sys.argv[1:], 'dhv', ['debug', 'help', 'version'])
    except getopt.GetoptError:
        Usage()
        sys.exit(2)

    for o, a in options:
        if o in ("-d", "--debug"):
            debug = True
        if o in ("-h", "--help"):
            Usage()
            sys.exit()
        if o in ("-v", "--version"):
            print('stepper.py Version 1.0')
            sys.exit()

    # Degrees to move (float). Can be positive or negative value
    if len(args) > 0 :
        degrees = float(args[0])
    else:
        Usage()
        sys.exit(-2)

    # Timing in millisecond for each step. Default is 10.0 milliseconds
    if len(args) > 1 :
        timing = float(args[1])
        if timing < 1.0 :
            print('Timing value incorrect. Needs to be 1.0 milliseconds or greater')
            sys.exit(-1)
            
    main(degrees, timing)
