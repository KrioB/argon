#!/usr/bin/python3

# -------------------------------------------
# Argon One Case shutdown script
# ver 1.0
# -------------------------------------------

import logging
from systemd.journal import JournalHandler
import sys
import smbus
import RPi.GPIO

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

log.info("I2C bus {}".format(busId))

# Global variables
FanAddress = 0x1a
FanBus = smbus.SMBus(busId)

# Stop the fan
try:
    FanBus.write_byte(FanAddress, 0)
    log.info("Fan stopped")
except Exception as err:
    log.error("Can not set fan\n{}".format(err))

# Turn off power supply
if len(sys.argv) > 1 and sys.argv[1] == "poweroff":
     try:
        FanBus.write_byte(FanAddress, 0xFF)
        log.info("Power off")
    except Exception as err:
        log.error("Can not power off\n{}".format(err))
