# Given a set of apps under a certain category,
# this scrapes them for all imported libraries and
# sanitizes the result to obtain a list of all
# imported third-party libraries (a first-party library is a module
# that is part of the app that is imported)

import os
import sys

from collections import OrderedDict
import json

from util import *
from pyflakes import reporter as modReporter
from pyflakes.api import checkRecursive, iterSourceCode

from stdlib_list import stdlib_list

DEBUG = False

def debug(msg):
    if DEBUG:
        print(str(msg))

def group_by_app(a, ungrouped):
    grouped = OrderedDict()
    for src, i in ungrouped.items():
        if a in src:
            # want raw_imports AND imports since raw_imports is used
            # in the unused parsing as well
            libs = remove_dups(i)
            grouped[src] = libs
    return grouped

def get_src_dir(path):
    dirs = path.split('/')
    script_idx = len(dirs)
    src_dir = "/".join(dirs[0:script_idx-1])
    return src_dir

# either return the app if the src dir is the app dir
# or return the dir above the source dir
def get_super_dir(app, path):
    if get_src_dir(path) == app:
        return app
    else:
        dirs = path.split('/')
        script_idx = len(dirs)
        super_dir = "/".join(dirs[0:script_idx-2])
        return super_dir

def get_top_pkg_name(name):
    if name.count('.') >= 1:
        mod = name.split('.')
        return mod[0]
    else:
        return ""

# this assumes path is a subdirectory of app
def get_top_pkg_from_path(app, path):
    app_comps = app.split("/")
    path_comps = path.split("/")
    return path_comps[len(app_comps)]

# we only want to store the top-level package
def get_pkg_names(app, target):
    print("Extracting package names for "+target)
    pkgs = []
    for lib in app[target]:
        tlp = get_top_pkg_name(lib)
        if lib == "RPi.GPIO":
            # let's make an exception for RPi.GPIO -- that's the pkg name
            tlp = lib
        elif lib.startswith("Image"):
            # apparently, you can import all of PIL or just subpkgs directly
            # so just rename any PIL subpkg to PIL
            tlp = "PIL"
        elif lib.startswith("tk"):
            # same with Tkinter
            tlp = "Tkinter"
        elif tlp == "":
            tlp = lib
        pkgs.append(tlp)
    return remove_dups(pkgs)

def get_subdir_srcs(subdir):
    srcs = []
    # will want to look at the contents of the entire directory
    files = os.listdir(subdir)
    for f in files:
        if not f.startswith("."):
            srcs.append(subdir+"/"+f)
    return srcs

def replace_fp_mod(app, super_dir, src_dir, imp, srcs_dict, visited):
    # let's get all the individual components of the import
    mods = imp.split(".")

    mod = ""
    supermod = ""
    single_imp = False
    src_dir_imp = False
    sibling_dir_imp = False
    higher_dir_imp = False
    pref = ""
    if len(mods) == 1:
        # we're importing a single name
        single_imp = True
        mod = mods[0]
    else:
        if src_dir.endswith("/"+mods[0]):
            src_dir_imp = True
            # we're importing a submodule from the src_dir
            # cut off the top-level module and keep all submodules
            mod = "/".join(mods[1:])
            supermod = "/".join(mods[1:len(mods)-1])
        elif super_dir.endswith("/"+mods[0]):
            sibling_dir_imp = True
            # we're importing a submodule from a sibling directory
            mod = "/".join(mods[1:])
            supermod = "/".join(mods[1:len(mods)-1])
        elif "/"+mods[0]+"/" in super_dir:
            higher_dir_imp = True
            # we're importing a submodule from a higher-up directory
            # this also means that neither src_dir nor super_dir are
            # the right prefix, so let's prune it
            mod = "/".join(mods)
            pref = super_dir[:super_dir.find("/"+mods[0])]
            supermod = "/".join(mods[:len(mods)-1])
        elif mods[0] == "" and mods[1] == "":
            sibling_dir_imp = True
            # we're importing a ..submodule from the sibling_dir
            mod = "/".join(mods[2:])
            supermod = "/".join(mods[2:len(mods)-1])
        elif mods[0] == "":
            src_dir_imp = True
            # we're importing a .module from the src_dir
            mod = "/".join(mods[1:])
            supermod = "/".join(mods[1:len(mods)-1])
        else:
            # we're probably importing from some other dir in the app dir
            mod = "/".join(mods)
            supermod = "/".join(mods[:len(mods)-1])

    py_file = ""
    subdir = ""
    obj_mod = ""
    sibling_py_file = ""
    sibling_subdir = ""
    sibling_obj_mod = ""
    higher_py_file = ""
    higher_subdir = ""
    higher_obj_mod = ""
    subdir_init_file = ""
    sibling_init_file = ""
    if single_imp:
        # we're importing a single module
        # so we need to check if it's a py file in the src dir or
        # a subdir
        py_file = src_dir+"/"+mod+".py"
        subdir = src_dir+"/"+mod
        subdir_init_file = subdir+"/__init__.py"
    elif src_dir_imp:
        debug("scr_dir_imp")
        # we're importing a module from the src dir
        # so we need to check if it's a py file in the src dir,
        # a subdir, or if the low-level pkg is actually an object
        # contained in a higher-level module
        py_file = src_dir+"/"+mod+".py"
        subdir = src_dir+"/"+mod
        if supermod != "":
            obj_mod = src_dir+"/"+supermod+".py"
        # we might be importing an attribute defined in __init__.py
        # so treat the obj_mod as the src_dir
        else:
            obj_mod = src_dir+"/__init__.py"

        subdir_init_file = subdir+"/__init__.py"
    elif sibling_dir_imp:
        debug("sibling_dir_imp")
        # we're importing a module from a sibling dir
        # so we need to check if it's a py file in the sibling dir,
        # a subdir, or if the low=level pkg is actually an object
        # contained in a higher-level module
        sibling_py_file = super_dir+"/"+mod+".py"
        sibling_subdir = super_dir+"/"+mod
        if supermod != "":
            sibling_obj_mod = super_dir+"/"+supermod+".py"
        else:
            # we might be importing an attribute defined in __init__.py
            # so treat the obj_mod as the src_dir
            sibling_obj_mod = super_dir+"/__init__.py"

        subdir_init_file = sibling_subdir+"/__init__.py"
    elif higher_dir_imp:
        debug("higher_dir_imp")
        # we're importing a module from a dir that's higher than the sibling
        # so we need to check if it's a py file in the higher dir,
        # a subdir, or if the low=level pkg is actually an object
        # contained in a higher-level module
        higher_py_file = pref+"/"+mod+".py"
        higher_subdir = pref+"/"+mod
        if supermod != "":
            higher_obj_mod = pref+"/"+supermod+".py"
        # we might be importing an attribute defined in __init__.py
        # so treat the obj_mod as the src_dir
        else:
            higher_obj_mod = pref+"/__init__.py"

        subdir_init_file = higher_subdir+"/__init__.py"
    else:
        debug("undetermined import")
        # we're not sure where we're importing from
        # let's try all generic possibilities
        py_file = src_dir+"/"+mod+".py"
        subdir = src_dir+"/"+mod
        sibling_py_file = super_dir+"/"+mod+".py"
        sibling_subdir = super_dir+"/"+mod
        if supermod != "":
            obj_mod = src_dir+"/"+supermod+".py"
            sibling_obj_mod = super_dir+"/"+supermod+".py"
            subdir_init_file = src_dir+"/"+supermod+"/__init__.py"
            sibling_init_file = super_dir+"/"+supermod+"/__init__.py"
        else:
            # we might be importing an attribute defined in __init__.py
            # so treat the obj_mod as the src_dir
            obj_mod = src_dir+"/__init__.py"
            sibling_obj_mod = super_dir+"/__init__.py"
            sibling_init_file = sibling_subdir+"/__init__.py"
            subdir_init_file = subdir+"/__init__.py"

    debug("Looking at "+py_file+", "+sibling_py_file+", "+higher_py_file+", "+obj_mod+", "+sibling_obj_mod+", "+higher_obj_mod+", "+subdir_init_file+", "+sibling_init_file+", "+subdir+", "+sibling_subdir+" and "+higher_subdir)

    # let's check if none of the possible imports exist
    if srcs_dict.get(py_file) == None and srcs_dict.get(sibling_py_file) == None and srcs_dict.get(higher_py_file) == None and srcs_dict.get(obj_mod) == None and srcs_dict.get(sibling_obj_mod) == None and srcs_dict.get(higher_obj_mod) == None and srcs_dict.get(subdir_init_file) == None and srcs_dict.get(sibling_init_file) == None and not os.path.isdir(subdir) and not os.path.isdir(sibling_subdir) and not os.path.isdir(higher_subdir):
        debug("0")
        return [imp]

    else:
        srcs = []
        if srcs_dict.get(py_file) != None:
            debug("1")
            srcs = [py_file]
        elif srcs_dict.get(sibling_py_file) != None:
            debug("2")
            srcs = [sibling_py_file]
        elif srcs_dict.get(higher_py_file) != None:
            debug("3")
            srcs = [higher_py_file]
        elif srcs_dict.get(obj_mod) != None:
            debug("4")
            srcs = [obj_mod]
        elif srcs_dict.get(sibling_obj_mod) != None:
            debug("5")
            srcs = [sibling_obj_mod]
        elif srcs_dict.get(higher_obj_mod) != None:
            debug("6")
            srcs = [higher_obj_mod]
        elif srcs_dict.get(subdir_init_file) != None:
            debug("7")
            srcs = [subdir_init_file]
        elif srcs_dict.get(sibling_init_file) != None:
            debug("8")
            srcs = [sibling_init_file]
        elif os.path.isdir(subdir):
            debug("9")
            srcs = iterSourceCode([subdir])
        elif os.path.isdir(sibling_subdir):
            debug("10")
            srcs = iterSourceCode([sibling_subdir])
        elif os.path.isdir(higher_subdir):
            debug("11")
            srcs = iterSourceCode([higher_subdir])

        l = []
        for src in srcs:
            if src in visited:
                print(src+" is imported recursively, so don't go deeper")
            else:
                visited.append(src)
                for m in srcs_dict[src]:
                    replacements = replace_fp_mod(app, get_super_dir(app, src), get_src_dir(src), m, srcs_dict, visited)
                    l.extend(replacements)
        return l

def replace_fp_mod_app(apps, a, target):
    print("Replacing the first-party imports for group: "+target)
    libs = []
    for src, i in apps[a][target].items():
        src_dir = get_src_dir(src)
        super_dir = get_super_dir(a, src)
        print(" *** "+src)
        for l in i:
            try:
                # add entry for each src once we've tried to replace it
                recurs_limit = []
                # want this check bc we want to make sure we stay
                # within the app directory
                tmp = replace_fp_mod(a, super_dir, src_dir, l, apps[a]['raw_imports'], recurs_limit)

                # this is just to avoid printing redundant messages
                if not(len(tmp) == 1 and tmp[0] == l):
                    print("replacing "+l+" with "+str(tmp))
                libs.extend(tmp)
            except RecursionError:
                print("died trying to replace "+l+" in "+src)
                sys.exit(-1)
    return remove_dups(libs)

def call_native_proc(l):
    if "os.system" in l or "os.spawnlp" in l or "os.popen" in l or "subprocess.call" in l or "subprocess.Popen" in l or "subprocess.check_output" in l or "Popen" in l or "call(" in l:
        return True
    return False

# collect all the native calls so proc collection is only about
# parsing those lines
def scan_source_native(src):
    f = open(src, "r")
    lines = f.readlines()
    f.close()
    # these are the calls to native code that we've observed
    nats = []
    nextLn = ""
    for l in lines:
        clean = l.strip()
        if not clean.startswith("#") and call_native_proc(clean):
            debug("Found call to native proc in code: "+clean)
            # let's make sure the actual command isn't actually
            # on the next line
            if ")" not in clean:
                nextLn = clean
            else:
                nats.append(clean)
        elif nextLn != "":
            nats.append(nextLn+clean)
            nextLn = ""
    return nats

# collect all the shared lib loads so proc collection is only about
# parsing those lines
def scan_source_ctypes(src):
    f = open(src, "r")
    lines = f.readlines()
    f.close()
    # these are the calls to native code that we've observed
    hybs = []
    for l in lines:
        clean = l.strip()
        if not clean.startswith("#") and "CDLL" in clean:
            debug("Found shared lib load in code: "+clean)
            hybs.append(clean)
    return hybs

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
os.system("python2 -m pyflakes "+app_path+" > pyflakes-out/"+cat+"-py2-report.txt 2>&1")

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

write_map(imports_raw, "pyflakes-out/"+cat+"-imports.txt", perm="w+", sort=True)
write_map(unused_raw, "pyflakes-out/"+cat+"-unused.txt", perm="w+", sort=True)

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

    # group the raw unused by app
    print("Grouping all unused by app")
    apps[a]['unused'] = group_by_app(a, unused_raw)

    # group the raw imports by app
    print("Grouping all imports by app")
    apps[a]['raw_imports'] = group_by_app(a, imports_raw)

    # iterate over the raw_imports to replace any pkg-level imports in
    # any "unused" __init__.py files
    if not a.endswith(".py"):
        for src, i in apps[a]['raw_imports'].items():
            new_i = []
            for l in i:
                mods = l.split(".")
                endidx = len(mods)-1
                # if we have an __init__.py file in the same pkg that has
                # unused imports we want to replace any of those in the
                # raw_imports entry for this src file
                init_unused = apps[a]['unused'].get(a+"/"+mods[0]+"/__init__.py")
                replaced = False
                if init_unused != None and len(init_unused) > 0:
                    debug("Source file: "+src+", lib: "+l)
                    debug(a+"/"+mods[0]+" "+str(init_unused))
                    for l_unused in init_unused:
                        mods_unused = l_unused.split(".")
                        endidx_unused = len(mods_unused)-1
                        if mods_unused[endidx_unused] == mods[endidx]:
                            new_i.append(mods[0]+"."+l_unused)
                            replaced = True
                            print("Replacing "+l+" with "+mods[0]+"."+l_unused+" in init for "+src)
                            break

                    if not replaced:
                        new_i.append(l)
                else:
                    new_i.append(l)

            apps[a]['raw_imports'][src] = new_i

    # iterate over the raw_imports to collect the ones that call native code/use ctypes
    print("Collecting apps that call a native process or are hybrid python-C")
    for src, i in apps[a]['raw_imports'].items():
        calls = []
        loads = []
        for l in i:
            if l == "os" or l == "subprocess" or l == "subprocess.call" or l == "subprocess.Popen":
                c = scan_source_native(src)
                if len(c) > 0:
                    calls.extend(c)
            elif l == "ctypes":
                lds = scan_source_ctypes(src)
                if len(lds) > 0:
                    loads.extend(lds)
        if len(calls) > 0:
            proc_srcs.append({src:calls})
        if len(loads) > 0:
            hybrid_srcs.append({src:loads})

    if len(proc_srcs) > 0:
        call_to_native[a] = proc_srcs

    if len(hybrid_srcs) > 0:
        hybrid[a] = hybrid_srcs

    # iterate over each source file's imports to find
    # the first-party imports
    if not a.endswith(".py"):
        # make sure to sort the sources to have a deterministic analysis
        apps[a]['raw_imports'] = OrderedDict(sorted(apps[a]['raw_imports'].items(), key=lambda t: t[0]))

        apps[a]['imports'] = replace_fp_mod_app(apps, a, 'raw_imports')
    else:
        # we can do this since the app name is the only source file in the raw imports
        apps[a]['imports'] = apps[a]['raw_imports'][a]

    # we only want to store the pkg names
    apps[a]['imports'] = get_pkg_names(apps[a], 'imports')

    # iterate over all imports and prune away all std lib imports
    print("Removing all python std lib imports")
    libs2 = stdlib_list("2.7")
    libs3 = stdlib_list("3.4")
    libs35 = stdlib_list("3.5")
    libs_3p = []
    for l in apps[a]['imports']:
        if l not in libs2 and l not in libs3 and l not in libs35:
            libs_3p.append(l)
    apps[a]['imports'] = libs_3p

    # iterate of each source's files imports to remove unused imports that actually appear
    # in the list of imports
    if not a.endswith(".py"):
        # make sure to sort the sources to have a deterministic analysis
        apps[a]['unused'] = OrderedDict(sorted(apps[a]['unused'].items(), key=lambda t: t[0]))

        apps[a]['unused'] = replace_fp_mod_app(apps, a, 'unused')
    else:
        # we can do this since the app name is the only source file in the raw imports
        apps[a]['unused'] = apps[a]['unused'][a]

    # remove the raw imports once we're done with all the parsing
    del apps[a]['raw_imports']

    # now we only want to store the pkg names
    apps[a]['unused'] = get_pkg_names(apps[a], 'unused')

    # if a pkg is under unused (possibly bc an app submodule doesn't
    # use it or some submodule is unused), but it also appears in imports
    # consider it used by the app, so remove it from unused
    pruned_unused = []
    for l in apps[a]['unused']:
        if l not in apps[a]['imports']:
            pruned_unused.append(l)

    apps[a]['unused'] = pruned_unused

write_map(call_to_native, "corpus/"+cat+"-call-native.txt", perm="w+", sort=True)
write_map(hybrid, "corpus/"+cat+"-hybrid-apps.txt", perm="w+", sort=True)

li = []
for a in apps:
    for i in sorted(apps[a]['imports']):
        li.append(i)

write_list_raw(li, "corpus/"+cat+"-libs.txt")

li = []
for a in apps:
    for i in sorted(apps[a]['unused']):
        li.append(i)

write_list_raw(li, "corpus/"+cat+"-unused-libs.txt")

# collect per-app libs and lib counts
lib_counts = OrderedDict()
p="w+"
for a in apps:
    write_list(apps[a]['imports'], "corpus/"+cat+"-libs-perapp.txt", name=a, perm=p)
    lib_counts[a] = len(apps[a]['imports'])
    if p == "w+":
        # want to set the perm to append after the first app
        p = "a+"

write_freq_map(lib_counts, filename="analysis/"+cat+"-lib-counts.txt", perm="w+")
