import os
import sys

from collections import OrderedDict

from pyflakes import reporter as modReporter
from pyflakes.api import checkRecursive, iterSourceCode
from stdlib_list import stdlib_list

from util import *

def extract_imports(cat, path):
    f = open("pyflakes-out/"+cat+"-py3-report.txt", "a+")
    reporter = modReporter.Reporter(f, f)
    # num = number of warnings, imps = used imports, un = unused imports
    num, imps, un = checkRecursive([path], reporter)
    f.close()

    # the modules in this list are likely written in python2 so run pyflakes
    # on python2
    os.system("python2 -m pyflakes "+path+" >> pyflakes-out/"+cat+"-py2-report.txt 2>&1")

    # now, let's parse the imports and unused
    py2_imps_f = "pyflakes-out/imports-py2.txt"
    py2_unused_f = "pyflakes-out/unused-py2.txt"
    if os.path.isfile(py2_imps_f) and os.path.isfile(py2_unused_f):
        imps_2 = read_map(py2_imps_f)
        un_2 = read_map(py2_unused_f)
        os.remove(py2_imps_f)
        os.remove(py2_unused_f)
    else:
        imps_2 = {}
        un_2 = {}

    # the py2 run of flakes probably finds imports found by the py3 run
    # let's merge the two dicts
    # see: https://stackoverflow.com/questions/38987/how-to-merge-two-python-dictionaries-in-a-single-expression#26853961
    imports_raw = {**imps, **imps_2}
    unused_raw = {**un, **un_2}

    if len(imports_raw) > 0:
        write_map(imports_raw, "pyflakes-out/"+cat+"-imports.txt", sort=True)
    if len(unused_raw) > 0:
        write_map(unused_raw, "pyflakes-out/"+cat+"-unused.txt", sort=True)

    return imports_raw, unused_raw

def group_by(g, ungrouped):
    grouped = OrderedDict()
    for src, i in ungrouped.items():
        if g in src:
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

def replace_fp_mod_group(grp_dict, g, target):
    print("Replacing the first-party imports for group: "+target)
    libs = []
    for src, i in grp_dict[target].items():
        src_dir = get_src_dir(src)
        super_dir = get_super_dir(g, src)
        print(" *** "+src)
        for l in i:
            try:
                # add entry for each src once we've tried to replace it
                recurs_limit = []
                # want this check bc we want to make sure we stay
                # within the app directory
                tmp = replace_fp_mod(g, super_dir, src_dir, l, grp_dict['raw_imports'], recurs_limit)

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
        if not clean.startswith("#") and ("CDLL" in clean or "LoadLibrary(" in clean):
            debug("Found shared lib load in code: "+clean)
            hybs.append(clean)
    return hybs

def remove_stdlib_imports(grp):
    libs2 = stdlib_list("2.7")
    libs3 = stdlib_list("3.4")
    libs35 = stdlib_list("3.5")
    libs_3p = []
    for l in grp['imports']:
        if l not in libs2 and l not in libs3 and l not in libs35:
            libs_3p.append(l)
    return libs_3p

def replace_unused_init_imports(raw_imports, unused, path):
    replaced_imps = OrderedDict()
    for src, i in raw_imports.items():
        new_i = []
        for l in i:
            mods = l.split(".")
            endidx = len(mods)-1
            # if we have an __init__.py file in the same pkg that has
            # unused imports we want to replace any of those in the
            # raw_imports entry for this src file
            init_unused = unused.get(path+"/"+mods[0]+"/__init__.py")
            replaced = False
            if init_unused != None and len(init_unused) > 0:
                debug("Source file: "+src+", lib: "+l)
                debug(path+"/"+mods[0]+" "+str(init_unused))
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

        replaced_imps[src] = new_i
    return replaced_imps
