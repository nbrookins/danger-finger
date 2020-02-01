#!/bin/sh
wget -qO - https://files.openscad.org/OBS-Repository-Key.pub | apt-key add -
echo "deb https://download.opensuse.org/repositories/home:/t-paul/xUbuntu_18.04/ ./" > /etc/apt/sources.list.d/openscad.list