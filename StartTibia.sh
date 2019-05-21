#!/bin/bash

# This script starts Tibia with a set of provided libraries.
# (the file libc6/README explains where those libraries came from)

# Please try calling this script instead of calling ./Tibia
# in case of problems while starting Tibia.
# (a typical error this script might help with is the dreaded
# "Floating point exception" right after starting Tibia)

./libc6/ld-linux.so.2 --library-path ./libc6 ./Tibia
