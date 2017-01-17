# Gather statistics about the collected IoT apps

import sys
import os
from collections import OrderedDict

from util import *

# remove an existing stats file since we'll want to override it
if os.path.isfile(STATS_FILE):
    os.remove(STATS_FILE)

# get all the apps
apps = dict()
apps['visual'] = read_set("visual-apps.txt")
apps['audio'] = read_set("audio-apps.txt")
apps['env'] = read_set("env-apps.txt")
apps['multi'] = read_set("multi-apps.txt")

# get total number of distinct apps
distinct_apps = get_distinct(apps)

num_apps = len(distinct_apps)

write_val(str(num_apps)+", "+str(len(apps['visual']))+", "+str(len(apps['audio']))+", "+str(len(apps['env']))+", "+str(len(apps['multi'])), "total apps, visual, audio, env, multi")

# get all the libs
libs = OrderedDict()
libs['visual'] = read_set("visual-libs.txt")
libs['audio'] = read_set("audio-libs.txt")
libs['env'] = read_set("env-libs.txt")
libs['multi'] = read_set("multi-libs.txt")

# count the number of distinct libs among all lib sets
distinct_libs = get_distinct(libs)
num_libs = len(distinct_libs)

write_val(num_libs, "libs")
write_list_raw(distinct_libs, "all-libs.txt")

# also want to know how many distinct libs were found in each category
for cat in libs:
    dist = get_distinct_cat(cat, libs)
    write_val(len(dist), cat+" libs")

# get all common libs
common_libs = get_common(libs)

# get all category-unique libs
only_libs = get_unique(libs)

# traverse the multi libs
# add any lib that appears in any of the unique lists
# to that list
# otherwise, consider it a common lib
for l in libs['multi']:
    if only_libs['visual'].get(l) != None:
        only_libs['visual'][l] += 1
    elif only_libs['audio'].get(l) != None:
        only_libs['audio'][l] += 1
    elif only_libs['env'].get(l) != None:
        only_libs['env'][l] += 1
    elif common_libs.get(l) != None:
        common_libs[l] += 1
    else:
        common_libs[l] = 1

# now print the aggregate common and unique libs
write_val(len(common_libs), "common libs")
write_freq_map(common_libs)

write_list_raw(common_libs.keys(), "common-libs.txt")

write_val(len(only_libs['visual']), "visual-only libs")
write_freq_map(only_libs['visual'])
write_val(len(only_libs['audio']), "audio-only libs")
write_freq_map(only_libs['audio'])
write_val(len(only_libs['env']), "env-only libs")
write_freq_map(only_libs['env'])

# get all the unused libs
unused = OrderedDict()
unused['visual'] = read_set("visual-unused-libs.txt")
unused['audio'] = read_set("audio-unused-libs.txt")
unused['env'] = read_set("env-unused-libs.txt")
unused['multi'] = read_set("multi-unused-libs.txt")

# count the frequency of each unused lib
distinct_unused = OrderedDict()
for cat in unused:
    distinct_unused = count_freq(unused[cat], distinct_unused)

write_val(len(distinct_unused), "unused libs")
write_freq_map(distinct_unused)
write_list_raw(distinct_unused.keys(), "all-unused-libs.txt")

'''

# get all external process
ext_calls = dict()

for cat, l in libs.items():
    for i in l:
        if is_native(i):
            lib = get_lib_name(i)
            if ext_calls.get(lib) == None:
                ext_calls[lib] = 1
            else:
                ext_calls[lib] += 1

write_val(len(ext_calls), "external process calls")
write_freq_map(ext_calls)
'''
