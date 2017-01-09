# Given a set of apps under a certain category,
# this scrapes them for all imported libraries and
# sanitizes the result to obtain a list of all
# imported third-party libraries (a first-party library is a module
# that is part of the app that is imported)

import os
import sys
import copy

from collections import OrderedDict
import json

from util import write_map, read_map, remove_dups
from pyflakes import reporter as modReporter
from pyflakes.api import checkRecursive

def make_mod_name(prefix, name):
    return prefix+"/"+name+".py"

def replace_fp_mod(prefix, mod, d):
    n = make_mod_name(prefix, mod)
    if d.get(n) == None:
        return [mod]
    else:
        l = []
        for m in d[n]:
            tmp = replace_fp_mod(prefix, m, d)
            l.extend(tmp)
        return l

# pass in the category: visual, audio or env
cat = sys.argv[1]

# expect apps to be located in apps/cat/
app_path = "apps/"+cat+"/"

f = open(cat+"-pyflakes-py3-report.txt", "w+")
reporter = modReporter.Reporter(f, f)
num, imps, un = checkRecursive([app_path], reporter)
f.close()

# the modules in this list are likely written in python2 so run pyflakes
# on python2
os.system("python2 -m pyflakes "+app_path+" > "+cat+"-pyflakes-py2-report.txt")

# let's organize our imports by app
app_list = os.listdir(app_path)

apps = OrderedDict()
for a in app_list:
    if not a.startswith('.'):
        app = app_path+a
        apps[app] = OrderedDict()

# now, let's parse the imports and unused, and organize them by app
imps_2 = read_map(cat+"-flakes-imports-py2.txt")
un_2 = read_map(cat+"-flakes-unused-py2.txt")

# the py2 run of flakes probably finds imports found by the py3 run
# let's merge the two dicts
# see: https://stackoverflow.com/questions/38987/how-to-merge-two-python-dictionaries-in-a-single-expression#26853961
imports_raw = {**imps, **imps_2}
unused_raw = {**un, **un_2}

os.remove(cat+"-flakes-imports-py2.txt")
os.remove(cat+"-flakes-unused-py2.txt")

print("Number of "+cat+" apps being scraped: "+str(len(apps)))

# iterate through all apps to organize the imports
for a in apps:
    for src, i in imports_raw.items():
        if a in src:
            libs = remove_dups(i)

            if a.endswith(".py"):
                # single-module apps don't have first-party imports
                apps[a]['imports'] = libs
            else:
                if apps[a].get('imports') == None:
                    apps[a]['imports'] = OrderedDict()
                apps[a]['imports'][src] = libs

    # iterate over each source file's imports to find
    # the first-party imports
    if not a.endswith(".py"):
        # make sure to sort the sources to have a deterministic analysis
        apps[a]['imports'] = OrderedDict(sorted(apps[a]['imports'].items(), key=lambda t: t[0]))

        libs = []
        print("current app: "+a)
        for src, i in apps[a]['imports'].items():
            for l in i:
                # TODO: add checks for subprocess.call, subprocess.Popen
                # os.system, os.spawn, etc
                if apps[a]['imports'].get(make_mod_name(a, l)) != None:
                    try:
                        tmp = replace_fp_mod(a, l, apps[a]['imports'])
                        print("replacing "+l+" with "+str(tmp))
                        libs.extend(tmp)
                    except RecursionError:
                        print("died trying to replace "+l+" in "+src)
                        sys.exit(-1)
                else:
                    libs.append(l)
        apps[a]['imports'] = remove_dups(libs)

# remove all __init__.py unused imports since they aren't actually unused
for a in apps:
    for src, i in unused_raw.items():
        if a in src and not src.endswith("__init__.py"):
            libs = remove_dups(i)

            if a.endswith(".py"):
                apps[a]['unused'] = libs
            else:
                if apps[a].get('unused') == None:
                    apps[a]['unused'] = OrderedDict()
                apps[a]['unused'][src] = libs

write_map(apps, cat+"-app-imports.txt")
