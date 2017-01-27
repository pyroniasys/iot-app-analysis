# Given a set of apps under a certain category,
# this scrapes them for all imported libraries and
# sanitizes the result to obtain a list of all
# imported third-party libraries (a first-party library is a module
# that is part of the app that is imported)

import os
import sys
import subprocess

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

def get_c_libs(libs_path, cat):
    no_pip = []

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

    f = open(libs_path+cat+"-libs.txt", "r")
    libs = f.readlines()
    f.close()

    print("Number of libs in "+cat+": "+str(len(libs)))

    c_libs = []
    py_libs = []
    libs_3p = OrderedDict()
    for l in libs:
        lib = l.strip()
        try:
            subprocess.check_output(["pip", "install", "--no-deps", "--no-compile", "-t", "/tmp/"+lib, lib])

            print("--- "+lib)

            lib_path = "/tmp/"+lib

            if check_for_c_source(lib_path, lib):
                print("Found a C-implementation")
                c_libs.append(lib)
            else:
                imports_raw, unused_raw = extract_imports(cat, lib_path)

                imps = OrderedDict()

                # this means pyflakes didn't find any .py files in the source
                if len(imports_raw) == 0 and len(unused_raw) == 0:
                    print("No python sources found")
                    c_libs.append(lib)
                # this means pyflakes found a single empty __init__.py file
                elif len(imports_raw) == 1 and len(unused_raw) == 1 and imports_raw.get(lib_path+"/__init__.py") != None and len(imports_raw.get(lib_path+"/__init__.py")) == 0 and unused_raw.get(lib_path+"/__init__.py") != None and len(unused_raw.get(lib_path+"/__init__.py")) == 0:
                    print("C implementation likely elsewhere ")
                    c_libs.append(lib)
                else:
                    imps['unused'] = unused_raw
                    imps['raw_imports'] = imports_raw

                    # iterate over the raw_imports to replace any pkg-level
                    # imports in any "unused" __init__.py files
                    imps['raw_imports'] = replace_unused_init_imports(imps['raw_imports'], imps['unused'], lib_path)

                    # iterate over the raw_imports to collect the ones that use ctypes
                    # for libs, this means, if we find a ctypes.CDLL, we are calling
                    # into third-party C code
                    for src, i in imps['raw_imports'].items():
                        for l in i:
                            if l == "ctypes":
                                lds = scan_source_ctypes(src)
                                if len(lds) > 0:
                                    c_libs.append(lib)
                                    print("Found ctypes wrapper")
                                    break

                            elif l == "os" or l == "subprocess" or l == "subprocess.call" or l == "subprocess.Popen":
                                c = scan_source_native(src)
                                if len(c) > 0:
                                    c_libs.append(lib)
                                    print("Found call to native proc")
                                    break

                        c_libs = remove_dups(c_libs)

                        if lib not in c_libs:
                            # this is the main case where we need to replace libs etc
                            # make sure to sort the sources to have a deterministic analysis
                            imps['raw_imports'] = OrderedDict(sorted(imps['raw_imports'].items(), key=lambda t: t[0]))

                            imps['imports'] = replace_fp_mod_group(imps, lib_path, 'raw_imports')

                            # we only want to store the pkg names
                            imps['imports'] = get_pkg_names(imps, 'imports')

                            # iterate over all imports and prune away all std lib imports
                            print("Removing all python std lib imports")
                            imps['imports'] = remove_stdlib_imports(imps)

                            if len(imps['imports']) == 0:
                                print("No 3-p imports: pure python lib")
                                py_libs.append(lib)
                            else:
                                print("Found 3-p imports, so need further investigation")
                                libs_3p[lib] = imps['imports']

            # we don't care about unused imports at this point
        except subprocess.CalledProcessError:
            no_pip.append(lib)

    write_list_raw(no_pip, "corpus/"+cat+"-no-pip.txt")
    write_list_raw(c_libs, "corpus/"+cat+"-c-libs.txt")
    write_list_raw(p_libs, "corpus/"+cat+"-py-libs.txt")
    write_list_raw(libs_3p, "corpus/"+cat+"-3p-libs.txt")

get_c_libs("corpus/", "all")
