#!/bin/bash

CAT=$1

python3 lib-scraper.py $CAT > $CAT-lib-collect.out 2>&1
