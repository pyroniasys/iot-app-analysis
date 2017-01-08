# Given a set of apps under a certain category,
# this scrapes them for all imported libraries and
# sanitizes the result to obtain a list of all
# imported third-party libraries (a first-party library is a module
# that is part of the app that is imported)

import os
import sys

from util import write_map, read_map, sanitize_imports
from pyflakes import reporter as modReporter
from pyflakes.api import checkRecursive

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

# now, let's parse the imports and unused
imps_2 = read_map(cat+"-flakes-imports-py2.txt")
un_2 = read_map(cat+"-flakes-unused-py2.txt")

# the py2 run of flakes probably finds imports found by the py3 run
# let's dedup
imports = dict()
unused = dict()

# merge the two dicts
# see: https://stackoverflow.com/questions/38987/how-to-merge-two-python-dictionaries-in-a-single-expression#26853961
imports_raw = {**imps, **imps_2}
unused_raw = {**un, **un_2}

os.remove(cat+"-flakes-imports-py2.txt")
os.remove(cat+"-flakes-unused-py2.txt")

# remove all __init__.py unused imports since they aren't actually unused
unused = dict()
for src, i in unused_raw.items():
    if not src.endswith("__init__.py"):
        unused[src] = sanitize_imports(i)

write_map(unused, cat+"-unused-src.txt")

# replace any first-party imports with the corresponding 3p imports
imports = dict()
for src, i in imports_raw.items():
    # iterate over each source file's imports to find
    # the first-party imports

    # first sanitize and get the actual library name
    libs = sanitize_imports(i)
    imports[src] = libs

write_map(imports, cat+"-imports-src.txt")
