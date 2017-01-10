#!/bin/bash

CAT=$1

python3 lib-scraper.py $CAT > $CAT-collect.out
