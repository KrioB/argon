#!/usr/bin/python3
import sys
import smbus
import RPi.GPIO

revision = RPi.GPIO.RPI_REVISION
if revision == 2 or revision == 3:
	FanBus = smbus.SMBus(1)
else:
	FanBus = smbus.SMBus(0)

FanAddress = 0x1a

FanBus.write_byte(FanAddress, 0)

if len(sys.argv) > 1 and sys.argv[1] == "poweroff":
    FanBus.write_byte(FanAddress, 0xFF)