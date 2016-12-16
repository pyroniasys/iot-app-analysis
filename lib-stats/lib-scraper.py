# Given a set of apps under a certain category,
# this scrapes them for all imported libraries and
# sanitizes the result to obtain a list of all
# imported third-party libraries (an first-party library is a module
# that is part of the app that is imported)

import os
import sys

from util import write_map

# pass in the category: visual, audio or env
cat = sys.argv[1]

# expect apps to be located in apps/cat/
app_path = "apps/"+cat+"/"

# scrape the apps using 2 grep commands
grep_imports = "cd "+app_path+"; grep -R --include \*.py \"^import \" >> ../../"+cat+"-libs-raw-imports.txt"
grep_froms = "cd "+app_path+"; grep -R --include \*.py \"^from [a-zA-Z0-9]* import \" >> ../../"+cat+"-libs-raw-froms.txt"

os.system(grep_imports)
os.system(grep_froms)

# read the raw imports
f = open(cat+"-libs-raw-imports.txt", "r")
raw_imports = f.readlines()
f.close()

# extract the libs from the import statements, map them to their modules
module_imports = dict()
for i in raw_imports:
    imp = i.rstrip().split(":") # module in [0], import stmt in [1]
    module = imp[0]
    stmt = imp[1]

    # first see if the import is aliasing

    # get the libs
    toks = stmt.split(" ")
    if toks[0] != "import":
        print("Unexpected import statement")
        sys.exit(-1)

    del toks[0]
    libs = []
    for l in toks:
        if l != "as":
            libs.append(l.strip(","))

    if module_imports.get(module) == None:
        module_imports[module] = libs
    else:
        module_imports[module] += libs

for m in module_imports:
    print(m+": ")
    for l in module_imports[m]:
        print(l)
