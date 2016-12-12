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

def write_map(m, name):
    d = OrderedDict(sorted(m.items(), key=itemgetter(1), reverse=True))
    f = open(name+"-freq.txt", "w+")
    f.write("Total # libs = "+str(len(d))+"\n")
    f.write(json.dumps(d, indent=4)+"\n")
    f.close()
