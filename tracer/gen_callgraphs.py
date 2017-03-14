# Given a set of apps under a certain category,
# this executes them while running a tracing function (tracer/tracer.py)
# which collects the callgraph of the app

import os
import sys

from collections import OrderedDict

# pass in the category: visual, audio or env
cat = sys.argv[1]

# expect apps to be located in apps/cat/
app_path = "apps/"+cat+"/"

# let's organize our imports by app
apps_list = os.listdir(app_path)

apps = []
for a in app_list:
    if not a.startswith('.'):
        app = app_path+a
        apps.append(app)

print("Number of "+cat+" apps being run: "+str(len(apps)))

# for now only collect the callgraph for those apps
for a in apps:
    if a.endswith(".py"):
