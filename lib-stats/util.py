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
    s_clean = []
    for i in s:
        s_clean.append(i.rstrip())
    return s_clean

def is_native(lib):
    if ("- os" in lib) or ("- CLI" in lib) or (" - subprocess" in lib):
        return True
    return False

def count_freq(to_count, m=None):
    if m == None:
        m = dict()
    for i in to_count:
        lib = i
        if m.get(lib) == None:
            m[lib] = 1
        else:
            m[lib] += 1
    return m

# expects a dict containing lists for different categories of the same data
def get_distinct(d):
    dis = []
    # iterate over the dict
    for cat in d:
        l = get_distinct_cat(cat, d)
        dis.extend(l)
    return remove_dups(dis)

def get_distinct_cat(cat, d):
    dis = []
    for lib in d[cat]:
        if lib not in dis:
            dis.append(lib)
    return dis

# we don't want to include libs['multi'] in this count since
# we'll be counting domain-unique libs that are used in
# multi-domain apps as non-unique
def get_common(libs):
    # need to check all pairs to get the right count
    common_libs = dict()
    for lib in libs['visual']:
        if lib in libs['audio'] or lib in libs['env']:
            if common_libs.get(lib) == None:
                common_libs[lib] = 1
            else:
                common_libs[lib] += 1

    for lib in libs['audio']:
        if lib in libs['visual'] or lib in libs['env']:
            if common_libs.get(lib) == None:
                common_libs[lib] = 1
            else:
                common_libs[lib] += 1

    for lib in libs['env']:
        if lib in libs['visual'] or lib in libs['audio']:
            if common_libs.get(lib) == None:
                common_libs[lib] = 1
            else:
                common_libs[lib] += 1

    return common_libs

# we don't want to include libs['multi'] in this count since
# we'll be counting domain-unique libs that are used in
# multi-domain apps as non-unique
def get_unique(libs):
    # need to check all pairs to get the right count
    unique_libs = dict()
    vis = dict()
    for lib in libs['visual']:
        if lib not in libs['audio'] and lib not in libs['env']:
            if vis.get(lib) == None:
                vis[lib] = 1
            else:
                vis[lib] += 1
    unique_libs['visual'] = vis

    aud = dict()
    for lib in libs['audio']:
        if lib not in libs['visual'] and lib not in libs['env']:
            if aud.get(lib) == None:
                aud[lib] = 1
            else:
                aud[lib] += 1
    unique_libs['audio'] = aud

    env = dict()
    for lib in libs['env']:
        if lib not in libs['visual'] and lib not in libs['audio']:
            if env.get(lib) == None:
                env[lib] = 1
            else:
                env[lib] += 1
    unique_libs['env'] = env
    return unique_libs

# remove duplicate entries from a list
def remove_dups(l):
    return sorted(list(set(l)))

def read_map(filename):
    with open(filename, "r") as f:
        m = json.loads(f.read(), object_pairs_hook=OrderedDict)
    return m

def write_val(v, name):
    f = open("stats.txt", "a+")
    f.write("Number of "+name+": "+str(v)+"\n")
    f.close()

def write_list(l, filename, name=None):
    f = open(filename, "a+")
    if name != None:
        f.write(str(name)+":\n")
    f.write(json.dumps(l, indent=4)+"\n")
    f.close()

def write_list_raw(l, filename):
    f = open(filename, "w+")
    for i in l:
        f.write(str(i)+"\n")
    f.close()

def write_map(m, filename, name=None, perm="a+"):
    f = open(filename, perm)
    if name != None:
        f.write(str(name)+":\n")
    f.write(json.dumps(m, indent=4)+"\n")
    f.close()

def write_freq_map(m):
    d = OrderedDict(sorted(m.items(), key=itemgetter(1), reverse=True))
    write_map(d, "stats.txt")
