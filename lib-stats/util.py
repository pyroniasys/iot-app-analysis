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
    for cat in d:
        l = get_distinct_cat(cat, d)
        dis = list(set(dis + l))
    return dis

def get_distinct_cat(cat, d):
    dis = []
    for i in d[cat]:
        lib = get_lib_name(i)
        if lib not in dis:
            dis.append(lib)
    return dis

# typ should be either "sens", "proc" or "net"
def get_common(typ, libs):
    # need to check all pairs to get the right count
    common_libs = dict()
    for i in libs['vis-'+typ]:
        if i in libs['audio-'+typ] or i in libs['env-'+typ]:
            lib = get_lib_name(i)
            if common_libs.get(lib) == None:
                common_libs[lib] = 1
            else:
                common_libs[lib] += 1

    for i in libs['audio-'+typ]:
        if i in libs['vis-'+typ] or i in libs['env-'+typ]:
            lib = get_lib_name(i)
            if common_libs.get(lib) == None:
                common_libs[lib] = 1
            else:
                common_libs[lib] += 1

    for i in libs['env-'+typ]:
        if i in libs['vis-'+typ] or i in libs['audio-'+typ]:
            lib = get_lib_name(i)
            if common_libs.get(lib) == None:
                common_libs[lib] = 1
            else:
                common_libs[lib] += 1
    return common_libs

# typ should be either "sens", "proc" or "net"
def get_unique(typ, libs):
    # need to check all pairs to get the right count
    unique_libs = dict()
    vis = dict()
    for i in libs['vis-'+typ]:
        if i not in libs['audio-'+typ] and i not in libs['env-'+typ]:
            lib = get_lib_name(i)
            if vis.get(lib) == None:
                vis[lib] = 1
            else:
                vis[lib] += 1
    unique_libs['vis'] = vis

    aud = dict()
    for i in libs['audio-'+typ]:
        if i not in libs['vis-'+typ] and i not in libs['env-'+typ]:
            lib = get_lib_name(i)
            if aud.get(lib) == None:
                aud[lib] = 1
            else:
                aud[lib] += 1
    unique_libs['audio'] = aud

    env = dict()
    for i in libs['env-'+typ]:
        if i not in libs['vis-'+typ] and i not in libs['audio-'+typ]:
            lib = get_lib_name(i)
            if env.get(lib) == None:
                env[lib] = 1
            else:
                env[lib] += 1
    unique_libs['env'] = env
    return unique_libs

# remove duplicate entries from a list
def remove_dups(l):
    return list(set(l))

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

def write_map(m, filename, name=None):
    f = open(filename, "a+")
    if name != None:
        f.write(str(name)+":\n")
    f.write(json.dumps(m, indent=4)+"\n")
    f.close()

def write_freq_map(m):
    d = OrderedDict(sorted(m.items(), key=itemgetter(1), reverse=True))
    write_map(d, "stats.txt")
