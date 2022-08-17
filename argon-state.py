#!/usr/bin/python3

fan = -1
tmp = -1

try:
    with open("/tmp/argon-state", "r") as data:

        for line in data:
            pair = line.split("=")
            if pair[0] == "fan":
                try:
                    fan = int(float(pair[1]))
                except:
                    fan = -1

            if pair[0] == "tmp":
                try:
                    tmp = int(float(pair[1]))
                except:
                    tmp = -1
except:
    print("Can not load data\nChceck if argond service is working")

if fan == -1 or tmp == -1:
    print("Wrong data")
else:
    print("CPU:\t{}C\nFan:\t{}%".format(tmp, fan))
