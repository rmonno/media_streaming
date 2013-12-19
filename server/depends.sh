#!/bin/sh

echo "install dependencies"

SUDO=`which sudo`
$SUDO apt-get update
$SUDO apt-get install -y python-pip vlc

PIP=`which pip`
$SUDO $PIP install termcolor bottle watchdog requests

echo "install dependencies... done!"
