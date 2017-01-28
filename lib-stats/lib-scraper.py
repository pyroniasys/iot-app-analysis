# Given a set of apps under a certain category,
# this scrapes them for all imported libraries and
# sanitizes the result to obtain a list of all
# imported third-party libraries (a first-party library is a module
# that is part of the app that is imported)

import os
import sys
import subprocess
from queue import Queue

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

def get_libs_with_deps(top_lib, c_libs, py_libs, no_pip, call_native):
    queue = Queue()
    queue.put(top_lib)

    while not queue.empty():
        try:
            lib = queue.get()
            subprocess.check_output(["pip", "install", "--no-compile", "-t", "/tmp/"+lib, lib])

            print("--- "+lib)

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
                c_libs.append(top_lib)
            else:
                imports_raw, unused_raw = extract_imports(cat, lib_path)

                imps = OrderedDict()

                # this means pyflakes didn't find any .py files in the source
                if len(imports_raw) == 0 and len(unused_raw) == 0:
                    print("No python sources found")
                    c_libs.append(top_lib)
                # this means pyflakes found a single empty __init__.py file
                elif len(imports_raw) == 1 and len(unused_raw) == 1 and imports_raw.get(lib_path+"/__init__.py") != None and len(imports_raw.get(lib_path+"/__init__.py")) == 0 and unused_raw.get(lib_path+"/__init__.py") != None and len(unused_raw.get(lib_path+"/__init__.py")) == 0:
                    print("C implementation likely elsewhere (no imports)")
                    c_libs.append(top_lib)
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
                        c_libs.append(top_lib)

                    # iterate over the raw_imports to collect the ones that use ctypes
                    # for libs, this means, if we find a ctypes.CDLL, we are calling
                    # into third-party C code
                    for src, i in imps['raw_imports'].items():
                        for l in i:
                            if l == "ctypes":
                                lds = scan_source_ctypes(src)
                                if len(lds) > 0:
                                    c_libs.append(top_lib)
                                    print("Found ctypes wrapper")
                                    break

                            elif l == "os" or l == "subprocess" or l == "subprocess.call" or l == "subprocess.Popen":
                                c = scan_source_native(src)
                                if len(c) > 0:
                                    call_native.append(top_lib)
                                    print("Found call to native proc")
                                    break

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

                        if len(imps['imports']) == 0:
                            print("No 3-p imports: pure python lib")
                            py_libs.append(top_lib)
                        else:
                            print("Found 3-p imports, so we're going to add those to the queue")
                            clean = []
                            for l in imps['imports']:
                                # remove any 3p imports that are the lib itself
                                # remove any 3p imports that are in c_libs, py_libs
                                # remove any 3p imports of setuptools
                                if l != lib and l not in c_libs and l not in py_libs and l != "setuptools":
                                    queue.put(l)


            # we don't care about unused imports at this point
        except subprocess.CalledProcessError:
            no_pip.append(lib)

    c_libs = remove_dups(c_libs)
    call_native = remove_dups(call_native)

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

for l in libs:
    lib = l.strip()
    get_libs_with_deps(lib, c_libs, py_libs, no_pip, call_native)

write_list_raw(no_pip, "corpus/"+cat+"-no-pip.txt")
write_list_raw(call_native, "corpus/"+cat+"-ext-proc.txt")
write_list_raw(c_libs, "corpus/"+cat+"-c-libs.txt")
write_list_raw(py_libs, "corpus/"+cat+"-py-libs.txt")
write_map(scraped_3p, "corpus/"+cat+"-3p-libs.txt", perm="w+")
