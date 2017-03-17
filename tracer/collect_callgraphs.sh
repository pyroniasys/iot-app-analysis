#!/bin/bash

CAT=$1
mkdir -p callgraphs/logs
# pass in the result of pwd so we can run this script on any machine
python3 gen_callgraphs.py $CAT `pwd` > callgraphs/logs/$CAT\_log 2>&1

echo "Done"
