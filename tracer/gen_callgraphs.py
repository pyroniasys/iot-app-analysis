# Given a set of apps under a certain category,
# this executes them while running a tracing function (tracer/tracer.py)
# which collects the callgraph of the app

import os
import sys

from collections import OrderedDict

# pass in the category: visual, audio or env
cat = sys.argv[1]

# expect apps to be located in apps/cat/
app_path = "../lib-stats/apps/"+cat+"/"

# let's organize our imports by app
app_list = os.listdir(app_path)

apps = []
for a in app_list:
    if not a.startswith('.'):
        apps.append(a)

print("Number of "+cat+" apps being run: "+str(len(apps)))

# for now only collect the callgraph for those apps
for a in apps:
    if a.endswith(".py"):
        app = app_path+a
    else:
        app = app_path+a+"/"+a+".py"
    # meh, convert everything to python3.5 to normalize the analysis
    os.system("2to3 -w "+a)
    # now run the callgraph generator
    os.system("python3 -m tracer "+app)
