# Given a set of apps under a certain category,
# this executes them while running a tracing function (tracer/tracer.py)
# which collects the callgraph of the app

import subprocess
import time
import sys
import os
import signal

from collections import OrderedDict

from tracer import Tracer

APP_DIR = "../apps"
LIB_DIR = "../libs"

# pass in the category: visual, audio or env
cat = sys.argv[1]
callgraph_path = "callgraphs/"+cat

os.makedirs(callgraph_path, exist_ok=True)
os.makedirs("logs", exist_ok=True)

# get the tracer path in order to pass the right path to the
# callgraph generator
tracer_path = os.getcwd() # this allows us to run this script on any machine

# expect apps to be located in apps/cat/
app_path = APP_DIR+"/"+cat+"-py3"

# meh, convert everything to python3 to normalize the analysis
os.system("2to3 --output-dir="+app_path+" -w -n "+APP_DIR+"/"+cat)

# let's get a list of apps we want to analyze
app_list = os.listdir(app_path)

apps = []
for a in app_list:
    if not a.startswith('.'):
        apps.append(a)

# let's add our downloaded libs to the PYTHONPATH so we use the same libs
# as our import analysis
lib_list = os.listdir(LIB_DIR)
# move all libs to /tmp for a more general search path
if not os.path.isdir("/tmp/libs"):
    os.system("cp -r "+LIB_DIR+" /tmp")
# add each lib independently bc all libs and their dependencies are in
# top-level dirs created during the import analysis
for l in lib_list:
    sys.path.append("/tmp/libs/"+l)

# redirect stdout and stderr to the log file
LOG = "logs/"+cat+".log"
sys.stdout = open(LOG, "w+")
sys.stderr = open(LOG, "w+")

for a in apps:
    print("[collect_callgraphs] Collecting data for "+a)
    to_trace = []
    if a.endswith(".py"):
        app = app_path+"/"+a
        to_trace = [app]
    else:
        app = app_path+"/"+a+"/"+a+".py"
        if not os.path.isfile(app):
            # some apps use multiple disjoint scripts
            # so we want to trace each individually
            for m in os.listdir(app_path+"/"+a):
                if m.endswith(".py") and m != "setup.py":
                    to_trace.append(app_path+"/"+a+"/"+m)
        else:
            to_trace = [app]

    # now run the callgraph generator
    if len(to_trace) == 1:
        tr = Tracer(tracer_path, callgraph_path, to_trace)
    else:
        tr = Tracer(tracer_path, callgraph_path, to_trace, app=a)
    tr.start_tracer()

    # generate the callgraph
    tr.collect_call_graph()

print("[collect_callgraphs] Done")

# cleanup: remove the converted apps and close log file fds
os.system("rm -rf "+app_path)
sys.stdout.close()
sys.stderr.close()
