# Given a set of apps under a certain category,
# this scrapes them for all imported libraries and
# sanitizes the result to obtain a list of all
# imported third-party libraries (a first-party library is a module
# that is part of the app that is imported)

import os
import sys
import subprocess
from queue import Queue
import time

from collections import OrderedDict

from util import *
from import_scraper import *

# this goes through the entire lib hierarchy and looks for
# a C-implementation of the lib
def check_for_c_source(path, lib):
    c = search_c_source(path, lib)
    if len(c) > 0:
        return True
    return False

def check_ctypes_wrapper(imps):
    for src, i in imps.items():
        for l in i:
            if l == "ctypes":
                lds = scan_source_ctypes(src)
                if len(lds) > 0:
                    print("Found ctypes wrapper")
                    return True
    return False

def check_shared_libs(path, lib):
    shlibs = search_shared_libs(path, lib)
    if len(shlibs) > 0:
        return True
    return False

def check_ext_proc_calls(imps):
    for src, i in imps['raw_imports'].items():
        for l in i:
            if l == "os" or l == "subprocess" or l == "subprocess.call" or l == "subprocess.Popen" or "os." in l:
                c = scan_source_native(src)
                if len(c) > 0:
                    print("Found call to native proc")
                    return True
    return False

def get_libs_with_deps(names, top_lib, lib, visited, clibs, shlibs, extproc):
    no_pip = []

    print("---- "+lib)

    # this covers the case in which we download a lib we've seen in
    # a previous call of get_libs_with_deps
    if lib in clibs or lib in shlibs or lib in extproc:
        print("Found "+lib+" in c libs, shared libs, or ext proc calls")
        c = []
        s = []
        n = []
        if lib in clibs:
            c = [lib]
        if lib in shlibs:
            s = [lib]
        if lib in extproc:
            n = [lib]
        return c, s, n, no_pip

    # the alternative name
    if names.get(lib) != None and names[lib] != "":
        downl = names[lib]
    else:
        downl = lib

    lib_path = "/tmp/"+lib

    # these two next cases cover downloaded dependencies
    if os.path.isdir("/tmp/"+top_lib+"/"+lib):
        lib_path = "/tmp/"+top_lib+"/"+lib
    elif os.path.isfile("/tmp/"+top_lib+"/"+lib+".py"):
        lib_path = "/tmp/"+top_lib+"/"+lib+".py"

    try:
        if not os.path.isdir(lib_path) and not os.path.isfile(lib_path):
            time.sleep(5) # sleep 5s to make sure we're not clobbering pip
            print("Downloading "+downl)
            if downl.startswith("https"):
                os.system("wget -q -P /tmp/"+lib+" --no-directories "+downl)
            else:
                subprocess.check_output(["pip3", "install", "-qq", "--no-compile", "-t", "/tmp/"+lib, downl])

            if lib == "RPi.GPIO":
                # make an exception for RPi.GPIO since it's the
                # only lib that only has a subpackage
                lib_path = lib_path+"/RPi/GPIO"
            elif os.path.isdir(lib_path+"/"+lib):
                # this means that the lib has its own dir
                lib_path = lib_path+"/"+lib
    except subprocess.CalledProcessError:
        no_pip.append(lib)
        print("Did not install through pip: "+lib)
        return [], [], [], no_pip

    if check_for_c_source(lib_path, lib):
        print("Found a C-implementation")
        return [lib], [], [], []
    else:
        print("Searching for imports in path: "+lib_path)

        imports_raw, unused_raw = extract_imports(cat, lib_path, perm="a+")

        imps = OrderedDict()

        # this means pyflakes didn't find any .py files in the source
        if len(imports_raw) == 0 and len(unused_raw) == 0:
            print("No python sources found")
            return [lib], [], [], []
        # this means pyflakes found a single empty __init__.py file
        elif len(imports_raw) == 1 and len(unused_raw) == 1 and imports_raw.get(lib_path+"/__init__.py") != None and len(imports_raw.get(lib_path+"/__init__.py")) == 0 and unused_raw.get(lib_path+"/__init__.py") != None and len(unused_raw.get(lib_path+"/__init__.py")) == 0:
            print("C implementation likely elsewhere (no imports)")
            return [lib], [], [], []
        else:
            imps['unused'] = unused_raw
            imps['raw_imports'] = imports_raw

            # iterate over the raw_imports to replace any pkg-level
            # imports in any "unused" __init__.py files
            imps['raw_imports'] = replace_unused_init_imports(imps['raw_imports'], imps['unused'], lib_path)

            # at this point, if we've replaced the init imports
            # and the imports are still empty, we can be pretty
            # sure that we have a c implementation elsewhere
            if len(imps['raw_imports']) == 1 and imps['raw_imports'].get(lib_path+"/__init__.py") != None and len(imps['raw_imports'].get(lib_path+"/__init__.py")) == 0:
                print("C implementation likely elsewhere (with imports)")
                return [lib], [], [], []
            else:
                c_libs = []
                hybrid_libs = []
                call_native = []

                # check to see if this lib is a ctypes wrapper
                if check_ctypes_wrapper(imps['raw_imports']):
                    hybrid_libs.append(lib)

                if check_ext_proc_calls(imps):
                    call_native.append(lib)

                # this is the main case where we need to replace libs etc
                # make sure to sort the sources to have a deterministic analysis
                imps['raw_imports'] = OrderedDict(sorted(imps['raw_imports'].items(), key=lambda t: t[0]))

                imps['imports'] = replace_fp_mod_group(imps, lib_path, 'raw_imports', is_libs=True)

                # we only want to store the pkg names
                imps['imports'] = get_pkg_names(imps, 'imports')

                # let's do one more check for c sources at this point
                # in case we missed anything within the current lib pkg
                # remove any such libs from the imports
                clean = []
                for l in imps['imports']:
                    if check_for_c_source(lib_path, l):
                        c_libs.append(l)
                    elif check_shared_libs(lib_path, l):
                        hybrid_libs.append(l)
                    else:
                        clean.append(l)

                imps['imports'] = clean

                # iterate over all imports and prune away all std lib imports
                print("Removing all python std lib imports")
                imps['imports'] = remove_stdlib_imports(imps)

                if len(imps['imports']) == 0 or lib in c_libs:
                    print("No 3-p imports, or lib is C after all")
                    return c_libs, hybrid_libs, call_native, []
                else:
                    print("Found 3-p imports -- more analysis")

                    for l in imps['imports']:
                        # remove any 3p imports that are the lib itself
                        # remove any 3p imports of setuptools
                        if l != lib and l != "setuptools":
                            l1 = l
                            # get rid of the annoying pip parse errors
                            if l.startswith("__") and l.endswith("__"):
                                pass
                            elif l.startswith("_"):
                                l1 = l[1:]
                            if l1 in visited:
                                print(l1+" has already been analyzed")
                            else:
                                visited.append(l1)
                                # let's start adding package exceptions
                                if l1 == "ntlm":
                                    names[l] = "python-ntlm"
                                elif l1 == "OpenSSL":
                                    names[l] = "pyOpenSSL"
                                c, hyb, n, np = get_libs_with_deps(names, top_lib, l1, visited, clibs, shlibs, extproc)
                                c_libs.extend(c)
                                hybrid_libs.extend(hyb)
                                call_native.append(n)
                                no_pip.extend(np)

                return c_libs, hybrid_libs, call_native, no_pip


#### MAIN ###

cat = sys.argv[1]

# cleanup before we start
imps_f = "pyflakes-out/"+cat+"-imports.txt"
unused_f = "pyflakes-out/"+cat+"-unused.txt"
py3_report_f = "pyflakes-out/"+cat+"-py3-report.txt"
py2_report_f = "pyflakes-out/"+cat+"-py2-report.txt"
if os.path.isfile(imps_f):
    os.remove(imps_f)
if os.path.isfile(unused_f):
    os.remove(unused_f)
if os.path.isfile(py3_report_f):
    os.remove(py3_report_f)
if os.path.isfile(py2_report_f):
    os.remove(py2_report_f)

f = open("corpus/"+cat+"-libs.txt", "r")
libs = f.readlines()
f.close()

print("Number of libs in "+cat+": "+str(len(libs)))

c_libs = []
call_native = []
hybrid_libs = []
no_pip = []
lib_names = OrderedDict()
for l in libs:
    pair = l.split(",")
    lib = pair[0].strip()
    lib_names[lib] = ""
    if len(pair) == 2:
         lib_names[lib] = pair[1].strip()
    recurs_limit = []
    find_pip_name(lib)
    c, hyb, native, np = get_libs_with_deps(lib_names, lib, lib, recurs_limit, c_libs, hybrid_libs, call_native)

    if len(c) > 0:
        c_libs.append(lib)
    if len(hyb) > 0:
        hybrid_libs.append(lib)
    if len(native) > 0:
        call_native.append(lib)
    if len(np) > 0:
        no_pip.extend(np)

write_list_raw(no_pip, "corpus/"+cat+"-no-pip.txt")
write_list_raw(call_native, "corpus/"+cat+"-ext-proc.txt")
write_list_raw(c_libs, "corpus/"+cat+"-c-libs.txt")
write_list_raw(hybrid_libs, "corpus/"+cat+"-shared-libs.txt")
