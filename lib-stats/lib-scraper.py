# Given a set of apps under a certain category,
# this scrapes them for all imported libraries and
# sanitizes the result to obtain a list of all
# imported third-party libraries (an first-party library is a module
# that is part of the app that is imported)

import os
import sys

from util import write_map, read_map
from pyflakes import reporter as modReporter
from pyflakes.api import checkRecursive

# pass in the category: visual, audio or env
cat = sys.argv[1]

# expect apps to be located in apps/cat/
app_path = "apps/"+cat+"/"

reporter = modReporter._makeDefaultReporter()
num, imps, unused, py2 = checkRecursive([app_path], reporter)

# the modules in this list are likely written in python2 so run pyflakes
# on python2
os.system("python2 -m pyflakes "+app_path)

# now, let's parse the imports and unused
imps_2 = read_map(cat+"-flakes-imports-py2.txt")
unused_2 = read_map(cat+"-flakes-unused-py2.txt")

# the py2 run of flakes probably finds imports found by the py3 run
# let's dedup
imported_libs = dict()
unused_libs = dict()
