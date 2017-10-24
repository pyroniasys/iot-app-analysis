import json
from collections import OrderedDict

def read_set(name):
    s_f = open(name, "r")
    s = s_f.readlines()
    s_f.close()
    s_clean = []
    for i in s:
        s_clean.append(i.rstrip())
    return s_clean

def read_map(filename):
    with open(filename, "r") as f:
        m = json.loads(f.read(), object_pairs_hook=OrderedDict)
    return m

def write_val(v, name, filename, perm="a+"):
    f = open(filename, perm)
    f.write("Number of "+name+": "+str(v)+"\n")
    f.close()

def write_str(v, s, filename, perm="a+"):
    f = open(filename, perm)
    f.write(s+": "+str(v)+"\n")
    f.close()

def write_list(l, filename, name=None, perm="a+"):
    f = open(filename, perm)
    if name != None:
        f.write(str(name)+":\n")
    f.write(json.dumps(l, indent=4)+"\n")
    f.close()

# TODO: merp, switch the default permission to "a+"
def write_list_raw(l, filename, perm="w+", sort=True):
    f = open(filename, perm)
    li = l
    if sort:
        li = sorted(l)
    for i in li:
        f.write(str(i)+"\n")
    f.close()

def write_map(m, filename, name=None, perm="a+", sort=False):
    f = open(filename, perm)
    if name != None:
        f.write(str(name)+":\n")
    d = m
    if sort:
        d = OrderedDict(sorted(m.items(), key=lambda t: t[0]))
    f.write(json.dumps(d, indent=4)+"\n")
    f.close()

# sort dict by values in descreasing order, then keys in regular order
# From http://stackoverflow.com/questions/9919342/sorting-a-dictionary-by-value-then-key
def write_freq_map(m, filename, perm="a+"):
    d = sort_freq_map(m)
    write_map(d, filename, perm=perm)
