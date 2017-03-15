#!/bin/bash

CAT=$1
APPS=$HOME/Research/lib-sandboxing/lib-stats/apps/$CAT
mkdir -p callgraphs/logs
python3 gen_callgraphs.py $CAT >> callgraphs/logs/$CAT\_log 2>&1

echo "Done"
