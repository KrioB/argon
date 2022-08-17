#!/usr/bin/python3

import smbus
import RPi.GPIO
#import os
import time


def loadConfiguration():

    defCurve = [[0, 100]]

    configuration = {
        "time": 5,
        "curve": []
    }

    try:
        confFile = open(ConfigurationFile, "r")
    except:
        configuration["curve"] = defCurve
        return configuration

    for line in confFile.readlines():

        tmpLine = line.strip()
        if not tmpLine:
            continue
        if tmpLine[0] == "#":
            continue
        pair = tmpLine.split("=")
        if len(pair) != 2:
            continue

        k = pair[0]
        v = pair[1]

        try:
            k = int(round(float(k)))
            if k < 0:
                k = 0
            elif k > 100:
                k = 100

        except ValueError:
            if not k in configuration:
                continue

        except:
            continue

        try:
            v = int(round(float(v)))

        except:
            continue

        if k in configuration:
            configuration[k] = v

        else:
            if v <= 0:
                v = 0
            elif v <= 25:
                v = 25
            elif v >= 100:
                v = 100

            configuration["curve"].append([k, v])

    confFile.close()

    if len(configuration["curve"]) > 1:
        configuration["curve"].sort(key=lambda x: x[0] * 1000 + x[1], reverse=False)

        i = 1
        while i < len(configuration["curve"]):
            if configuration["curve"][i-1][0] == configuration["curve"][i][0]:
                configuration["curve"].pop(i)
            else:
                i = i + 1

    if len(configuration["curve"]) == 1:
        if configuration["curve"][0][1] == 0:
            configuration["curve"][0][0] = 100
        else:
            configuration["curve"][0][0] = 0

    if len(configuration["curve"]) == 0:
        configuration["curve"] = defCurve

    return configuration


def getTemperature():

    temperature = 100

    try:
        tFile = open(TemperatureFile, "r")
    except:
        return temperature

    try:
        value = tFile.readline()
        value = int(round(int(value)/1000))
    except:
        value = 100

    tFile.close()
    temperature = value

    return temperature


def setFanSpeed(speed):

    FanBus.write_byte(FanAddress,speed)


revision = RPi.GPIO.RPI_REVISION
if revision == 2 or revision == 3:
	FanBus = smbus.SMBus(1)
else:
	FanBus = smbus.SMBus(0)

FanAddress = 0x1a

TemperatureFile = "/sys/class/thermal/thermal_zone0/temp"
ConfigurationFile = "argond.conf"

conf = loadConfiguration()

steps = len(conf["curve"])


if steps == 1:
    setFanSpeed(conf["curve"][0][1])
else:

    t0 = 0
    p0 = 0

    while True:
        t = getTemperature()

        if t > t0:
            s = conf["curve"][p0][1]
            for p in range(p0, steps, 1):
                if t < conf["curve"][p][0]:
                    break
                else:
                    s = conf["curve"][p][1]
                    p0 = p

            setFanSpeed(s)

        elif t < t0:
            s = conf["curve"][p0][1]
            for p in range(p0, -1, -1):
                if t > conf["curve"][p][0]:
                    break
                else:
                    s = conf["curve"][p][1]
                    p0 = p

            setFanSpeed(s)

        t0 = t

        time.sleep(conf["time"])
