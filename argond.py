#!/usr/bin/python3

# -------------------------------------------
# Argon One Case main deamon script
# ver 1.0
# -------------------------------------------

import logging
from systemd.journal import JournalHandler
import sys
import smbus
import RPi.GPIO
import time

# Load configuration file
# Uses global ConfigurationFile
# Returns valid configuration
def loadConfiguration():

    # Default configuration
    defCurve = [[0, 100]]

    configuration = {
        "time": 10,
        "curve": []
    }

    try:
        # Try to open configuration file
        confFile = open(ConfigurationFile, "r")
    except:
        # Return default configuration
        log.warning("Can not open {}".format(ConfigurationFile))
        configuration["curve"] = defCurve
        return configuration

    # Read configuration file line by line
    for line in confFile.readlines():

        # Trim white characters
        tmpLine = line.strip()
        if not tmpLine:
            # Skip empty lines
            continue
        if tmpLine[0] == "#":
            # Skip comments
            continue
        pair = tmpLine.split("=")
        if len(pair) != 2:
            # Skip wrong lines
            log.warning("Can not read property from {}\n>{}<".format(ConfigurationFile, line))
            continue

        k = pair[0]
        v = pair[1]

        if k.isdigit() and v.isdigit():
            # Get (temperature, speed) point for curve property
            k = int(k)
            if k < 0:
                k = 0
            elif k > 100:
                k = 100

            v = int(v)
            if v <= 0:
                v = 0
            elif v <= 25:
                v = 25
            elif v >= 100:
                v = 100

            # Push point to curve
            configuration["curve"].append([k, v])

        elif k == "time" and v.isdigit():
            # Get value for time property
            v = int(v)
            if v <= 0:
                v = 0
            elif v >= 100:
                v = 100

            configuration["time"] = v

        else:
            # Key is wrong
            log.warning("Can not read property from {}\n>{}<".format(ConfigurationFile, line))
            continue

    confFile.close()

    # If curve has at least 2 points
    if len(configuration["curve"]) > 1:
        # Sort curve
        configuration["curve"].sort(key=lambda x: x[0] * 1000 + x[1], reverse=False)

        # Remove duplicates
        i = 1
        while i < len(configuration["curve"]):
            if configuration["curve"][i-1][0] == configuration["curve"][i][0]:
                configuration["curve"].pop(i)
            else:
                i = i + 1

    # If curve has exactly 1 point
    if len(configuration["curve"]) == 1:
        if configuration["curve"][0][1] == 0:
            # Set fan always off
            configuration["curve"][0][0] = 100
        else:
            # Set fan always on
            configuration["curve"][0][0] = 0

    # If curve has no points
    if len(configuration["curve"]) == 0:
        # Default curve
        configuration["curve"] = defCurve

    return configuration

# Get CPU temperature
# Uses global TemperatureFile
# Returns temperature in Celsius
def getTemperature():

    # Default temperature
    defTemperature = 100

    try:
        # Try to open temperature file
        tFile = open(TemperatureFile, "r")
    except:
        # Return default temperature
        log.warning("Can not open {}".format(TemperatureFile))
        return defTemperature

    try:
        temperature = tFile.readline()
        # Convert mili Celsius to Celsius
        temperature = int(round(int(temperature)/1000))
    except:
        # Return default temperature
        log.warning("Can not read temperature from {}".format(TemperatureFile))
        temperature = defTemperature

    tFile.close()

    return temperature

# Set fan speed
# Uses global FanBus, FanAddress
# Returns False or error message
def setFanSpeed(speed):

    success = True
    try:
        FanBus.write_byte(FanAddress, speed)
        log.info("Fan speed set to {}%".format(speed))
    except Exception as err:
        log.error("Can not set fan\n{}".format(err))
        success = False

    return success

# Save status in TMP
# Uses global StatusFile
# Returns False or error message
def updateStatus(t, s):

    success = True
    try:
        status = open(StatusFile, "w+")
        status.write("fan={}\ntmp={}".format(s, t))
        status.close()
    except Exception as err:
        log.error("Can not save status\n{}".format(err))
        success = False

    return success

# Configure logger
log = logging.getLogger(__name__)
log.addHandler(JournalHandler())
log.setLevel(logging.INFO)

# Check board revision to use connected I2C bus
revision = RPi.GPIO.RPI_REVISION
if revision == 2 or revision == 3:
    busId = 1
else:
    busId = 0

# Global variables
try:
    FanBus = smbus.SMBus(busId)
    log.info("I2C bus {}".format(busId))
except Exception as err:
    log.critical("Can not set up I2C bus {}\n{}".format(busId, err))
    sys.exit(1)

FanAddress = 0x1a
StatusFile = "/tmp/argon-state"
TemperatureFile = "/sys/class/thermal/thermal_zone0/temp"
ConfigurationFile = "/etc/argond.conf"

# Load configuration
conf = loadConfiguration()

log.info(conf)

steps = len(conf["curve"])
if steps == 1:
    # No curve, fan spins with constant speed
    setFanSpeed(conf["curve"][0][1])

    # Empty loop required
    # systemd tries to relaunch this script every time it crashes or finishes
    # this loop keeps process alive with minimum CPU work
    while True:
        t = getTemperature()
        updateStatus(t, s)

        time.sleep(3600)

t0 = 0
p0 = 0

# Main loop
while True:

    t = getTemperature()

    # CPU temperature is increasing
    if t > t0:
        p = p0
        for point in range(p0, steps, 1):
            if t < conf["curve"][point][0]:
                break
            else:
                p = point

    # CPU temperature is decreasing
    elif t < t0:
        p = p0
        for point in range(p0, -1, -1):
            if t > conf["curve"][point][0]:
                break
            else:
                p = point

    t0 = t

    s = conf["curve"][p][1]

    if p != p0:
        # Fan speed changed
        p0 = p

        # Set fan
        setFanSpeed(s)

    # Save status
    updateStatus(t, s)

    time.sleep(conf["time"])
