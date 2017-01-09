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

def group_by_app(a, apps, ungrouped, target, target2=None):
    libs = remove_dups(ungrouped)
    if a.endswith(".py"):
        # single-module apps don't have first-party imports
        if target2:
            apps[a][target2] = libs
        else:
            apps[a][target] = libs
    else:
        if apps[a].get(target) == None:
            apps[a][target] = OrderedDict()
        apps[a][target][src] = libs

def get_prefix(path):
    dirs = path.split('/')
    script_idx = len(dirs)
    prefix = "/".join(dirs[0:script_idx-1])
    return prefix

def get_supermod(name):
     if name.count('.') == 1:
        mod = name.split('.')
        return "/"+mod[0]
     else:
         return ""

def make_super_mod_name(prefix, name):
    supermod =  prefix+get_supermod(name)+".py"

    # this case is true if the module doesn't have a supermodule
    if supermod == prefix+".py":
        return ""

    return supermod

def make_mod_name(prefix, name):
    if name.count('.') == 1:
        mod = name.split('.')
        return prefix+"/"+mod[0]+"/"+mod[1]+".py"

    return prefix+"/"+name+".py"

def replace_fp_mod(prefix, mod, d, visited):
    n = make_mod_name(prefix, mod)
    s = make_super_mod_name(prefix, mod)
    print("Looking at "+n+" and "+s)
    if d.get(n) == None and d.get(s) == None:
        # we only want to store the top-level package
        tlp = get_supermod(mod)
        if tlp == "":
           tlp = mod
        else:
            tlp = tlp.lstrip("/")
        return [tlp]
    else:
        insuper = False
        if d.get(n) != None:
            mo = n
        elif d.get(s) != None:
            insuper = True
            mo = s

        if mo in visited:
            print(mo+" is imported recursively, so don't go deeper")
            return []
        else:
            visited.append(mo)
            l = []
            for m in d[mo]:
                next_mod = prefix+get_supermod(mod)
                if insuper:
                    next_mod = prefix

                tmp = replace_fp_mod(next_mod, m, d, visited)
                l.extend(tmp)
            return l

def replace_fp_mod_app(app, target):
    print("Replacing the first-party imports for group: "+target)
    libs = []
    for src, i in app[target].items():
        pref = get_prefix(src)
        print(" *** "+src)
        for l in i:
            try:
                # add entry for each src once we've tried to replace it
                recurs_limit = []
                tmp = replace_fp_mod(pref, l, app['raw_imports'], recurs_limit)
                print("replacing "+l+" with "+str(tmp))
                libs.extend(tmp)
            except RecursionError:
                print("died trying to replace "+l+" in "+src)
                sys.exit(-1)
    return remove_dups(libs)

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

#write_map(imports_raw, cat+"-flakes-imports.txt")
#write_map(unused_raw, cat+"-flakes-unused.txt")

os.remove(cat+"-flakes-imports-py2.txt")
os.remove(cat+"-flakes-unused-py2.txt")

print("Number of "+cat+" apps being scraped: "+str(len(apps)))

# iterate through all apps to organize the imports
for a in apps:
    print("--- current app: "+a)
    for src, i in imports_raw.items():
        if a in src:
            # want raw_imports AND imports since raw_imports is used
            # in the unused parsing as well
            group_by_app(a, apps, i, 'raw_imports', 'imports')

    # iterate over each source file's imports to find
    # the first-party imports
    if not a.endswith(".py"):
        # make sure to sort the sources to have a deterministic analysis
        apps[a]['raw_imports'] = OrderedDict(sorted(apps[a]['raw_imports'].items(), key=lambda t: t[0]))

        apps[a]['imports'] = replace_fp_mod_app(apps[a], 'raw_imports')

    # remove all __init__.py unused imports since they aren't actually unused
    for src, i in unused_raw.items():
        if a in src and not src.endswith("__init__.py"):
            group_by_app(a, apps, i, 'unused')

    # iterate of each source's files imports to remove unused imports that actually appear
    # in the list of imports
    if not a.endswith(".py"):
        # make sure to sort the sources to have a deterministic analysis
        apps[a]['unused'] = OrderedDict(sorted(apps[a]['unused'].items(), key=lambda t: t[0]))

        apps[a]['unused'] = replace_fp_mod_app(apps[a], 'unused')

        # remove the raw imports once we're done with all the parsing
        del apps[a]['raw_imports']

write_map(apps, cat+"-app-imports.txt")
