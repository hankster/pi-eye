#! /usr/bin/env python

"""
eye-scan.py - A program to test the Pi Eye

This is a simple program to check the operation of the Eye. It does a left-right scan and takes some pictures.

For more information about the program type eye-scan.py -h

"""

__author__ = "Henry S. Magnuski"
__copyright__ = "Copyright 2017, Henry S. Magnuski"
__credits__ = [""]
__license__ = "MIT"
__version__ = "1.0.0"
__date__ = "2017-06-22"
__maintainer__ = "Henry S. Magnuski"
__email__ = "hank.magnuski@gmail.com"
__status__ = "Prototype"

import os
import sys
import time
import math
import getopt
import Xlib
import Xlib.display
import RPi.GPIO as GPIO
from picamera.array import PiRGBArray
from picamera import PiCamera
from stepper import stepper

def Usage():
    print('Usage: eye-scan.py -d -h -v --debug --debugv --dv --help --stepangle=degrees --steprange=degrees --version')

def Help():
    Usage()    
    print('\nThe following are command-line options:\n')
    print('-d, --debug\t\tPrint debugging information.')
    print('--debugv, --dv\t\tEnable visual space and display debugging.')
    print('-h, --help\t\tPrint help information.')
    print('--stepangle=degrees\tDegrees to rotate for each new camera position. Default=5.0 degrees')
    print('--steprange=degrees\tDegrees to rotate left and right for field of view. Default=45.0 degrees')
    print('-v, --version\t\tPrint version information')

# Debug options
debug = False

# The main visual array to be displayed and processed
visualDebug = False

# Define camera window size, parameters
cameraWidth = 1920.0
cameraHeight = 1080.0
cameraHflip = True
cameraVflip = True

# Range to scan and step amount (in degrees) and time (milliseconds) for each step
degreesRange = 45.0
degreesStep = 5.0
degreesTime = 10.0
degreesMoved = 0.0
degreesLock = True

# Main program for image capture
def main():

    global debug
    global visualDebug
    global degreesMoved


    if debug :
        print('Camera: width = %6.1f, height = %6.1f' % (cameraWidth, cameraHeight))

    # Start our scan going to the left
    stepDirection = -degreesStep
    stepTime = degreesTime
    loop = True
            
    camera = PiCamera()
    camera.hflip = cameraHflip
    camera.vflip = cameraVflip
    camera.resolution = (int(cameraWidth), int(cameraHeight))
    camera.start_preview()
    # Camera warm-up time
    time.sleep(2)

    while loop :

        # Grab an image from the camera
        if debug :
            print('Capture image')

        camera.capture('eye-scan%+06.2f.jpg' % degreesMoved, use_video_port=True)
            
        # Move the camera by some fixed angle. If degreesRange is zero, don't move at all.
        if degreesRange > 1.0 :
            degreesMoved = degreesMoved + stepper(stepDirection, stepTime, degreesLock)
            print('Degrees moved: %6.2f' % degreesMoved)
            
        # If we reach the left boundary, switch scan directions
        if degreesRange > 1.0 and degreesMoved < -degreesRange :
            stepDirection = -stepDirection
            # Move the camera back to the starting point plus stepDirection
            print('Returning to original position, starting opposite scan')
            degreesMoved = degreesMoved + stepper(stepDirection-degreesMoved, stepTime, degreesLock)
            print('Degrees moved: %6.2f' % degreesMoved)
        # If we've reached the right boundary, we're done
        if degreesRange > 1.0 and degreesMoved > degreesRange :
            loop = False

    # Restore the position
    if degreesRange > 1.0 :
        degreesMoved = degreesMoved + stepper(-degreesMoved, degreesTime, False) 
        print('Degrees moved: %6.2f' % degreesMoved)

    # Clean up
    camera.close()
    print('Bye from the Eye')

if __name__ == "__main__":

    try:
        options, args = getopt.getopt(sys.argv[1:], 'dhv', ['debug', 'dv', 'debugv', 'help', 'stepangle=', 'stepper', 'steprange=', 'version'])
    except getopt.GetoptError:
        Usage()
        sys.exit(2)

    for o, a in options:
        if o in ("-d", "--debug"):
            debug = True
        if o in ("--dv", "--debugv"):
            visualDebug = True
        if o in ("-h", "--help"):
            Help()
            sys.exit()
        if o in ("--stepangle"):
            degreesStep = float(a)
        if o in ("--steprange"):
            degreesRange = float(a)
        if o in ("-v", "--version"):
            print('eye-scan.py %s' % __version__)
            sys.exit()

    main()
    sys.exit(0)
