#!/bin/bash

PYTHONBIN=home.marcela.Research.lib-isolation.iot-app-analysis.callgraph-analysis.python35.python
sudo cp $PYTHONBIN /etc/apparmor.d/
sudo apparmor_parser -Cr /etc/apparmor.d/$PYTHONBIN
