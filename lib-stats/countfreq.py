# Creates a map of all libs in a category to their frequency

import sys

from util import *

to_count_p = sys.argv[1]
to_count = read_set(to_count_p)

to_count_name = get_name(to_count_p)

m = dict()

for i in to_count:
    # need to account for native
    lib = i.rstrip()
    if "-" in lib:
        lib = lib[:lib.find("-")-1]

    if m.get(lib) == None:
        m[lib] = 1
    else:
        m[lib] += 1

write_map(m, to_count_name)
