# Utility functions for the library stats scripts

import json
from collections import OrderedDict
from operator import itemgetter

def get_name(p):
    name = p[:p.find(".")]
    return name

def read_set(name):
    s_f = open(name, "r")
    s = s_f.readlines()
    s_f.close()
    return s

def is_native(lib):
    if ("- os" in lib) or ("- CLI" in lib) or (" - subprocess" in lib):
        return True
    return False

def get_lib_name(l):
    # need to account for native
    lib = l.rstrip()
    if is_native(l):
        lib = lib[:lib.find("-")-1]
    return lib

def count_freq(to_count):
    m = dict()
    for i in to_count:
        lib = get_lib_name(i)
        if m.get(lib) == None:
            m[lib] = 1
        else:
            m[lib] += 1
    return m

# expects a dict containing lists for different categories of the same data
def get_distinct(d):
    dis = []
    # iterate over the dict
    for cat, l in d.items():
        for i in l:
            lib = get_lib_name(i)
            if lib not in dis:
                dis.append(lib)
    return dis

def write_val(v, name):
    f = open("stats.txt", "a+")
    f.write("Number of "+name+": "+str(v)+"\n")
    f.close()

def write_freq_map(m):
    d = OrderedDict(sorted(m.items(), key=itemgetter(1), reverse=True))
    f = open("stats.txt", "a+")
    f.write(json.dumps(d, indent=4)+"\n")
    f.close()
