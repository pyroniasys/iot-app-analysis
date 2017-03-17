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

# pass in the category: visual, audio or env
cat = sys.argv[1]

# get the tracer path in order to pass the right path to the
# callgraph generator
tracer_path = sys.argv[2]

# expect apps to be located in apps/cat/
app_path = "../apps/"+cat+"-py3"

# meh, convert everything to python3.5 to normalize the analysis
os.system("2to3 --output-dir="+app_path+" -W -n ../apps/"+cat)

# let's get a list of apps we want to analyze
app_list = os.listdir(app_path)

apps = []
for a in app_list:
    if not a.startswith('.'):
        apps.append(a)

# for now only collect the callgraph for those apps
for a in apps:
    if a.endswith(".py"):
        app = app_path+"/"+a
    else:
        app = app_path+"/"+a+"/"+a+".py"
    # now run the callgraph generator
    tr = Tracer(tracer_path, app)
    tr.start_tracer()

    # generate the callgraph
    tr.collect_call_graph()

# cleanup: remove the converted apps
os.system("rm -rf "+app_path)
