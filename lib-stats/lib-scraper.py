# Given a set of apps under a certain category,
# this scrapes them for all imported libraries and
# sanitizes the result to obtain a list of all
# imported third-party libraries (a first-party library is a module
# that is part of the app that is imported)

import os
import sys

from collections import OrderedDict
import json

from util import write_map, read_map, remove_dups, write_list
from pyflakes import reporter as modReporter
from pyflakes.api import checkRecursive

from stdlib_list import stdlib_list

def group_by_app(a, ungrouped):
    grouped = OrderedDict()
    for src, i in ungrouped.items():
        if a in src:
            print(" *** "+src)
            # want raw_imports AND imports since raw_imports is used
            # in the unused parsing as well
            libs = remove_dups(i)
            grouped[src] = libs
    return grouped

def get_prefix(path):
    dirs = path.split('/')
    script_idx = len(dirs)
    prefix = "/".join(dirs[0:script_idx-1])
    return prefix

def get_supermod(name):
    if name.count('.') >= 1:
        mod = name.split('.')
        return "/"+mod[0]
    else:
        return ""

# we only want to store the top-level package
def get_pkg_names(app, target):
    print("Extracting package names for "+target)
    pkgs = []
    for lib in app[target]:
        # this is a case where we have a subpackage import
        if lib.count('.') > 1:
            mod = lib.split(".")
            tlp = mod[0]+"."+mod[1]
        else:
            tlp = get_supermod(lib)
            if tlp == "" or lib == "RPi.GPIO":
                # let's make an exception for RPi.GPIO -- that's the pkg name
                tlp = lib
            else:
                tlp = tlp.lstrip("/")
        pkgs.append(tlp)
    return remove_dups(pkgs)

def make_super_mod_name(prefix, name):
    supermod =  prefix+get_supermod(name)+".py"

    # this case is true if the module doesn't have a supermodule
    if supermod == prefix+".py":
        return ""

    return supermod

def make_mod_name(prefix, name):
    if name.count('.') >= 1:
        mod = name.split('.')
        return prefix+"/"+mod[0]+"/"+mod[1]+".py"

    return prefix+"/"+name+".py"

def replace_fp_mod(prefix, mod, d, visited):
    n = make_mod_name(prefix, mod)
    s = make_super_mod_name(prefix, mod)
    print("Looking at "+n+" and "+s)
    if d.get(n) == None and d.get(s) == None:
        return [mod]
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
        for l in i:
            try:
                # add entry for each src once we've tried to replace it
                recurs_limit = []
                tmp = replace_fp_mod(pref, l, app['raw_imports'], recurs_limit)

                # this is just to avoid printing redundant messages
                if not(len(tmp) == 1 and tmp[0] == l):
                    print("replacing "+l+" with "+str(tmp))
                libs.extend(tmp)
            except RecursionError:
                print("died trying to replace "+l+" in "+src)
                sys.exit(-1)
    return remove_dups(libs)

def call_native_proc(l):
    if "os.system" in l or "os.spawnlp" in l or "os.popen" in l or "subprocess.call" in l or "subprocess.Popen" in l:
        return True
    return False

def scan_source(src):
    f = open(src, "r")
    lines = f.readlines()
    f.close()
    # these are the calls to native code that we've observed
    for l in lines:
        clean = l.strip()
        if not clean.startswith("#") and call_native_proc(clean):
            print("Found call to native proc in code: "+clean)
            return True
    return False

# pass in the category: visual, audio or env
cat = sys.argv[1]

# expect apps to be located in apps/cat/
app_path = "apps/"+cat+"/"

f = open("pyflakes-out/"+cat+"-py3-report.txt", "w+")
reporter = modReporter.Reporter(f, f)
num, imps, un = checkRecursive([app_path], reporter)
f.close()

# the modules in this list are likely written in python2 so run pyflakes
# on python2
os.system("python2 -m pyflakes "+app_path+" > pyflakes-out/"+cat+"-py2-report.txt")

# let's organize our imports by app
app_list = os.listdir(app_path)

apps = OrderedDict()
for a in app_list:
    if not a.startswith('.'):
        app = app_path+a
        apps[app] = OrderedDict()

# now, let's parse the imports and unused, and organize them by app
imps_2 = read_map("pyflakes-out/"+cat+"-imports-py2.txt")
un_2 = read_map("pyflakes-out/"+cat+"-unused-py2.txt")

# the py2 run of flakes probably finds imports found by the py3 run
# let's merge the two dicts
# see: https://stackoverflow.com/questions/38987/how-to-merge-two-python-dictionaries-in-a-single-expression#26853961
imports_raw = {**imps, **imps_2}
unused_raw = {**un, **un_2}

write_map(imports_raw, "pyflakes-out/"+cat+"-imports.txt", perm="w+")
write_map(unused_raw, "pyflakes-out/"+cat+"-unused.txt", perm="w+")

os.remove("pyflakes-out/"+cat+"-imports-py2.txt")
os.remove("pyflakes-out/"+cat+"-unused-py2.txt")

print("Number of "+cat+" apps being scraped: "+str(len(apps)))

call_to_native = OrderedDict()
hybrid = OrderedDict()
# iterate through all apps to organize the imports
for a in apps:
    print("--- current app: "+a)
    proc_srcs = []
    hybrid_srcs = []

    # group the raw imports by app
    print("Grouping all imports by app")
    apps[a]['raw_imports'] = group_by_app(a, imports_raw)

    # iterate over the raw_imports to collect the ones that call native code/use ctypes
    print("Collecting apps that call a native process or are hybrid python-C")
    for src, i in apps[a]['raw_imports'].items():
        for l in i:
            if l == "subprocess.call" or l == "subprocess.Popen":
                print("Call to native proc in "+src)
                proc_srcs.append(src)
            elif l == "os" or l == "subprocess":
                if scan_source(src):
                    proc_srcs.append(src)
            elif l == "ctypes":
                print("Use ctypes in "+src)
                hybrid_srcs.append(src)

    if len(proc_srcs) > 0:
        call_to_native[a] = remove_dups(proc_srcs)

    if len(hybrid_srcs) > 0:
        hybrid[a] = remove_dups(hybrid_srcs)

    # iterate over each source file's imports to find
    # the first-party imports
    if not a.endswith(".py"):
        # make sure to sort the sources to have a deterministic analysis
        apps[a]['raw_imports'] = OrderedDict(sorted(apps[a]['raw_imports'].items(), key=lambda t: t[0]))

        apps[a]['imports'] = replace_fp_mod_app(apps[a], 'raw_imports')
    else:
        # we can do this since the app name is the only source file in the raw imports
        apps[a]['imports'] = apps[a]['raw_imports'][a]

    # we only want to store the pkg names
    apps[a]['imports'] = get_pkg_names(apps[a], 'imports')

    # iterate over all imports and prune away all std lib imports
    print("Removing all python std lib imports")
    libs2 = stdlib_list("2.7")
    libs3 = stdlib_list("3.4")
    libs_3p = []
    for l in apps[a]['imports']:
        if not l in libs2 and not l in libs3:
            libs_3p.append(l)
    apps[a]['imports'] = libs_3p

    # remove all __init__.py unused imports since they aren't actually unused
    unused_raw_clean = OrderedDict()
    for src, i in unused_raw.items():
        if not src.endswith("__init__.py"):
            unused_raw_clean[src] = i

    # group the raw unused by app
    print("Grouping all unused by app")
    apps[a]['unused'] = group_by_app(a, unused_raw_clean)

    # iterate of each source's files imports to remove unused imports that actually appear
    # in the list of imports
    if not a.endswith(".py"):
        # make sure to sort the sources to have a deterministic analysis
        apps[a]['unused'] = OrderedDict(sorted(apps[a]['unused'].items(), key=lambda t: t[0]))

        apps[a]['unused'] = replace_fp_mod_app(apps[a], 'unused')

        # remove the raw imports once we're done with all the parsing
        del apps[a]['raw_imports']

    # now we only want to store the pkg names
    apps[a]['unused'] = get_pkg_names(apps[a], 'unused')

    # if a pkg is under unused (possibly bc an app submodule doesn't
    # use it or some submodule is unused), but it also appears in imports
    # consider it used by the app, so remove it from unused
    pruned_unused = []
    for l in apps[a]['unused']:
        if not l in apps[a]['imports']:
            pruned_unused.append(l)

    apps[a]['unused'] = pruned_unused

write_map(call_to_native, cat+"-call-native.txt", perm="w+")
write_map(hybrid, cat+"-hybrid-apps.txt", perm="w+")

f = open(cat+"-libs.txt", "w+")
for a in apps:
    for i in apps[a]['imports']:
        f.write(str(i)+"\n")
f.close()

f = open(cat+"-unused-libs.txt", "w+")
for a in apps:
    for i in apps[a]['unused']:
        f.write(str(i)+"\n")
f.close()
