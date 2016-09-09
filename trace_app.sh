#!/bin/bash

APP=$1
cp apptracer.py apps/$APP/
python3 apps/$APP/$APP.py > traces/logs/$APP_log
rm apps/$APP/apptracer.py

echo "Done"
