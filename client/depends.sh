#!/bin/sh

echo "install dependencies"

SUDO=`which sudo`
$SUDO apt-get update
$SUDO apt-get install -y python-pip vlc libicu48

PIP=`which pip`
$SUDO $PIP install termcolor

echo "install dependencies... done!"
