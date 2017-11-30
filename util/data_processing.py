# Utility functions for the library stats scripts

import os
from collections import OrderedDict

from util.util import sort_freq_map

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
def get_common(libs, cat1='visual', cat2='audio', cat3='env'):
    # need to check all pairs to get the right count
    common_libs = dict()
    for lib in libs[cat1]:
        if lib in libs[cat2] or lib in libs[cat3]:
            if common_libs.get(lib) == None:
                common_libs[lib] = 1
            else:
                common_libs[lib] += 1

    for lib in libs[cat2]:
        if lib in libs[cat1] or lib in libs[cat3]:
            if common_libs.get(lib) == None:
                common_libs[lib] = 1
            else:
                common_libs[lib] += 1

    for lib in libs[cat3]:
        if lib in libs[cat1] or lib in libs[cat2]:
            if common_libs.get(lib) == None:
                common_libs[lib] = 1
            else:
                common_libs[lib] += 1

    return common_libs

# we don't want to include libs['multi'] in this count since
# we'll be counting domain-unique libs that are used in
# multi-domain apps as non-unique
def get_unique(libs, cat1='visual', cat2='audio', cat3='env'):
    # need to check all pairs to get the right count
    unique_libs = dict()
    vis = dict()
    for lib in libs[cat1]:
        if lib not in libs[cat2] and lib not in libs[cat3]:
            if vis.get(lib) == None:
                vis[lib] = 1
            else:
                vis[lib] += 1
    unique_libs[cat1] = vis

    aud = dict()
    for lib in libs[cat2]:
        if lib not in libs[cat1] and lib not in libs[cat3]:
            if aud.get(lib) == None:
                aud[lib] = 1
            else:
                aud[lib] += 1
    unique_libs[cat2] = aud

    env = dict()
    for lib in libs[cat3]:
        if lib not in libs[cat1] and lib not in libs[cat2]:
            if env.get(lib) == None:
                env[lib] = 1
            else:
                env[lib] += 1
    unique_libs[cat3] = env
    return unique_libs

def get_top_n_freq(n, m, total):
    d = sort_freq_map(m)
    count = 0
    top = OrderedDict()
    for l, ct in d.items():
        if count == n:
            break
        freq = (ct/total)*100
        top[l] = freq
        count += 1
    return top

def get_top_n(n, m):
    d = sort_freq_map(m)
    count = 0
    top = OrderedDict()
    for l, ct in d.items():
        if count == n:
            break
        top[l] = ct
        count += 1
    return top

def count_overall_freq(m):
    overall_freq = dict()
    for k, v in m.items():
        for i in v.keys():
            if overall_freq.get(i) == None:
                overall_freq[i] = 1
            else:
                overall_freq[i] += 1
    return overall_freq
