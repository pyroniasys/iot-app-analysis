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
    is_c = False
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            if filename == lib+".c" or filename == lib+".cpp":
                is_c = True
                break
        if is_c:
            break
    return is_c

'''
# expect libs and their URLs to be located at
libs_path = "corpus/libs/"
# let's get all the categories
lib_lists = os.listdir(libs_path)

cats = OrderedDict()
for c_f in lib_lists:
    if not c_f.startswith('.'):
        cat = c_f.split("-")[0].strip()
        cats[cat] = OrderedDict()
'''

def get_libs_with_deps(names, top_lib, c_libs):
    is_c = False
    call_native = False
    no_pip = []
    queue = Queue()

    if names[top_lib] == "":
        queue.put(top_lib)
    else:
        queue.put(names[top_lib])

    downloaded = []
    while not queue.empty():
        try:
            lib = queue.get()
            downloaded.append(lib)

            if lib.startswith("http"):
                if lib.endswith(".gz"):
                    os.system("wget -q -O /tmp/"+name+".tar.gz --no-directories "+lib)
                    os.system("tar -xzfq /tmp/"+name+" /tmp/"+name+".tar.gz")
                else:
                    os.system("wget -q -P /tmp/"+name+" --no-directories "+lib)
            else:
                subprocess.check_output(["pip", "install", "--no-deps", "--no-compile", "-t", "/tmp/"+lib, lib])

            if lib == top_lib:
                print("--- "+lib)
            else:
                print("------ "+lib)

            lib_path = "/tmp/"+lib

            if lib == "RPi.GPIO":
                # make an exception for RPi.GPIO since it's the
                # only lib that only has a subpackage
                lib_path = lib_path+"/RPi/GPIO"
            elif os.path.isdir(lib_path+"/"+lib):
                # this means that the lib has its own dir
                lib_path = lib_path+"/"+lib

            if check_for_c_source(lib_path, lib):
                print("Found a C-implementation")
                is_c = True
            else:
                imports_raw, unused_raw = extract_imports(cat, lib_path)

                imps = OrderedDict()

                # this means pyflakes didn't find any .py files in the source
                if len(imports_raw) == 0 and len(unused_raw) == 0:
                    print("No python sources found")
                    is_c = True
                # this means pyflakes found a single empty __init__.py file
                elif len(imports_raw) == 1 and len(unused_raw) == 1 and imports_raw.get(lib_path+"/__init__.py") != None and len(imports_raw.get(lib_path+"/__init__.py")) == 0 and unused_raw.get(lib_path+"/__init__.py") != None and len(unused_raw.get(lib_path+"/__init__.py")) == 0:
                    print("C implementation likely elsewhere (no imports)")
                    is_c = True
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
                        is_c = True

                    # iterate over the raw_imports to collect the ones that use ctypes
                    # for libs, this means, if we find a ctypes.CDLL, we are calling
                    # into third-party C code
                    for src, i in imps['raw_imports'].items():
                        for l in i:
                            if l == "ctypes":
                                lds = scan_source_ctypes(src)
                                if len(lds) > 0:
                                    is_c = True
                                    print("Found ctypes wrapper")
                                    break

                            elif l == "os" or l == "subprocess" or l == "subprocess.call" or l == "subprocess.Popen":
                                c = scan_source_native(src)
                                if len(c) > 0:
                                    call_native = True
                                    print("Found call to native proc")
                                    break

                    # at this point, if is_c is True, we can just return
                    # because we know the lib is C
                    if is_c:
                        return is_c, call_native, []

                    if lib not in c_libs:
                        # this is the main case where we need to replace libs etc
                        # make sure to sort the sources to have a deterministic analysis
                        imps['raw_imports'] = OrderedDict(sorted(imps['raw_imports'].items(), key=lambda t: t[0]))

                        imps['imports'] = replace_fp_mod_group(imps, lib_path, 'raw_imports', is_libs=True)

                        # we only want to store the pkg names
                        imps['imports'] = get_pkg_names(imps, 'imports')

                        # iterate over all imports and prune away all std lib imports
                        print("Removing all python std lib imports")
                        imps['imports'] = remove_stdlib_imports(imps)

                        if len(imps['imports']) == 0 and lib == top_lib:
                            print("No 3-p imports: pure python lib")
                            is_c = False

                            return is_c, call_native, []
                        else:
                            print("Found 3-p imports, so we're going to add those to the queue")
                            clean = []
                            for l in imps['imports']:
                                # remove any 3p imports that are the lib itself
                                # remove any 3p imports that are in c_libs, py_libs
                                # remove any 3p imports of setuptools
                                if l != lib and l not in c_libs and l not in py_libs and l != "setuptools":
                                    to_add = l
                                    if names.get(l) != None and names[l] != "":
                                            to_add = names[l]

                                    if to_add not in downloaded:
                                        queue.put(to_add)
                                        downloaded.append(to_add)

            # we don't care about unused imports at this point
        except subprocess.CalledProcessError:
            no_pip.append(lib)

        time.sleep(5) # sleep 5s to make sure we're not clobbering pip

    return is_c, call_native, no_pip

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
py_libs = []
no_pip = []
call_native = []
lib_names = OrderedDict()
for l in libs:
    pair = l.split(",")
    lib = pair[0].strip()
    lib_names[lib] = ""
    if len(pair) == 2:
         lib_names[lib] = pair[1].strip()
    is_c, native, nopip = get_libs_with_deps(lib_names, lib, c_libs)

    if len(nopip) == 0:
        if is_c:
            c_libs.append(lib)
        else:
            py_libs.append(lib)
        if native:
            call_native.append(lib)
    else:
        no_pip.extend(nopip)

write_list_raw(no_pip, "corpus/"+cat+"-no-pip.txt")
write_list_raw(call_native, "corpus/"+cat+"-ext-proc.txt")
write_list_raw(c_libs, "corpus/"+cat+"-c-libs.txt")
write_list_raw(py_libs, "corpus/"+cat+"-py-libs.txt")
