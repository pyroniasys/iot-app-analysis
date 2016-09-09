#!/bin/bash

APP=$1
cp tracer.py apps/$APP/
mkdir -p callgraphs/logs
python3 apps/$APP/$APP.py > callgraphs/logs/$APP\_log
rm apps/$APP/tracer.py

echo "Done"
