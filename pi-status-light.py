import RPi.GPIO as GPIO
import time
import threading
import logging
from logging.handlers import TimedRotatingFileHandler
import os
import socket
import errno

version = "v0.0.1"
piHostname = socket.gethostname()

LedPin_1 = 27        # pin13 --- status light

led_thread_type = "none"    # Type of lighting thread to run. [none, all, rotate, breath fast, breath medium, breath slow, sparkle fast, sparkle medium, sparkle slow] This is to controll stopping thread

logging
log_path = "/var/log/pi-status-light/"
log_file = "pi-status-light.log"

## Set up the GPIO Pins
def setup():
    GPIO.setmode(GPIO.BCM)       # Numbers GPIOs by Broadcom numbering. (GPIO.Board) would nubmer by physical location.
    GPIO.setup(LedPin_1,GPIO.OUT)   # Set LedPin_1's mode is output

##
## Functions to handle diffferent lighting effects
##

def off_all():
    global led_thread_type
    led_thread_type = "none"
    GPIO.output(LedPin_1,GPIO.LOW)
    logger.info("Led Thread: All Off - (no thread started)")

def on_all():
    global led_thread_type
    global led_thread
    if led_thread_type!="all":
        led_thread_type = "all"
        try:                        # If led thread is runing then stop it.
            led_thread.isAlive()
            time.sleep(0.05)
            logger.info("Thread was running.. but should stop???")
            led_thread.join()
        except NameError:
            logger.info("Thread not running")
        
        led_thread = threading.Thread(target=start_thread_all) # Start new led thread
        led_thread.start()
    else:
        logger.info("Led Thread: All - alreaday running")
    time.sleep(1)

def on_breath(speed):
    global led_thread_type
    global led_thread
    global breath_speed
    breath_speed = speed # Update global variable to fast (0.5 sec) or slow (1 sec). Could be any number of seconds.
    if led_thread_type!="breath":
        led_thread_type = "breath"
        try:                        # If led thread is runing and not 'breath' then stop it.
            led_thread.isAlive()
            time.sleep(0.05)
            logger.debug("Thread was running.. but should stop???")
            led_thread.join()
        except NameError:
            logger.info("Thread not running")
        
        led_thread = threading.Thread(target=start_thread_breath) # Start new led thread
        led_thread.start()
    else:
        logger.info("Led Thread: breath - alreaday running - breath Speed %s secs", breath_speed) # If just updating breath_speed then we keep the breath thread running


## Functions for light pattern threads
def start_thread_all():
    def check_thread_type_and_sleep(thread_sleep):
        if led_thread_type == "all":
            time.sleep(thread_sleep)
            logger.debug(led_thread_type)
    logger.info("Led Thread: All - STARTED")
    while led_thread_type == "all":
        GPIO.output(LedPin_1,GPIO.HIGH)
        check_thread_type_and_sleep(1)
    logger.info("Led Thread: All - STOP")

def start_thread_breath():
    def check_thread_type_and_sleep(thread_sleep):
        if led_thread_type == "breath":
            time.sleep(thread_sleep)
            logger.debug(led_thread_type)
    # Set up LED pins to be PWM so we can change the brightness
    led_pwm_1 = GPIO.PWM(LedPin_1,1000)
    led_pwm_1.start(0)
    logger.info("Led Thread: breath - STARTED - Breath Speed %s secs", breath_speed)
    while led_thread_type == "breath":
        # led_value 20 to 100 (brighten)
        for pwm_value in range(20,101,1):
            led_pwm_1.ChangeDutyCycle(pwm_value)
            check_thread_type_and_sleep(breath_speed / 100)
        # led_value 100 to 20 (dimm)
        for pwm_value in range(100,20,-1):
            led_pwm_1.ChangeDutyCycle(pwm_value)
            check_thread_type_and_sleep(breath_speed / 100)
    led_pwm_1.stop()
    logger.info("Led Thread: breath - STOP")

##
## Logging
##
def log_create():
    global logger
    mkdir_p(log_path)
    format = "%(asctime)s.%(msecs)03d %(levelname)s %(process)d (%(name)s-%(threadName)s) %(message)s (linuxThread-%(thread)d)"
    logger = logging.getLogger("Rotating Log")
    logger.setLevel(logging.INFO)
    log_handler = TimedRotatingFileHandler(log_path + log_file, when="midnight", interval=1, backupCount=30)
    log_handler.setFormatter(logging.Formatter(format))
    logger.addHandler(log_handler)
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%m/%d/%Y %H:%M:%S")

def log_create_stdout():
    format = "%(asctime)s.%(msecs)03d %(levelname)s %(process)d (%(name)s-%(threadName)s) %(message)s (linuxThread-%(thread)d)"
    logging.basicConfig(format=format, level=logging.INFO, datefmt="%m/%d/%Y %H:%M:%S")

def mkdir_p(path):
    try:
        os.makedirs(path, exist_ok=True)  # Python>3.2
    except TypeError:
        try:
            os.makedirs(path)
        except OSError as exc: # Python >2.5
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else: raise


### Temp Test Code
def testcode():
    on_all()
    time.sleep(2)
    on_breath(1)


##
## Main Code for App
##

## Main loop, adds event handler for button press.
def loop():
    while True:
        time.sleep(1) # Don't do anything

## clean up GPIO pins
def destroy(): # Not woking! 
    GPIO.output(LedPin_1, GPIO.LOW)     # led_1 off
    GPIO.cleanup()                      # Release resource

if __name__ == '__main__':     # Program start from here
    try:
        log_create()
        logger.info("Starting up...")
        logger.info("pi-status-lights : version %s : STARTED", version)
        setup()
        testcode()
        loop()
    except KeyboardInterrupt:
        logger.info("pi-status-lights : version %s : EXIT", version)
        destroy()
    finally:
        logger.info("pi-status-lights : version %s : EXIT", version)
        destroy()
