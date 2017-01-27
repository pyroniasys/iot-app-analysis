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
apps['visual'] = read_set("corpus/visual-apps.txt")
apps['audio'] = read_set("corpus/audio-apps.txt")
apps['env'] = read_set("corpus/env-apps.txt")
apps['multi'] = read_set("corpus/multi-apps.txt")

# get total number of distinct apps
distinct_apps = get_distinct(apps)

num_apps = len(distinct_apps)

write_val(str(num_apps)+", "+str(len(apps['visual']))+", "+str(len(apps['audio']))+", "+str(len(apps['env']))+", "+str(len(apps['multi'])), "total apps, visual, audio, env, multi")

# get all the libs
libs = OrderedDict()
libs['audio'] = read_set("corpus/audio-libs.txt")
libs['env'] = read_set("corpus/env-libs.txt")
libs['multi'] = read_set("corpus/multi-libs.txt")
libs['visual'] = read_set("corpus/visual-libs.txt")

# count the number of distinct libs among all lib sets
distinct_libs = get_distinct(libs)
num_libs = len(distinct_libs)
num_imports = len(libs['audio'])+len(libs['env'])+len(libs['multi'])+len(libs['visual'])

write_val(num_libs, "distinct 3p libs")
write_list_raw(distinct_libs, "corpus/all-libs.txt")

avg_lib_per_app = "%.1f" % (num_imports/num_apps)
write_str(avg_lib_per_app, "Avg number of 3p imports per app")

'''
# also want to know how many distinct libs were found in each category
for cat in libs:
    dist = get_distinct_cat(cat, libs)
    write_val(len(dist), cat+" libs")
'''

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
#write_val(len(common_libs), "common libs")
write_freq_map(common_libs, filename="analysis/common-lib-freq.txt", perm="w+")

write_list_raw(common_libs.keys(), "corpus/common-libs.txt")

#write_val(len(only_libs['audio']), "audio-only libs")
write_freq_map(only_libs['audio'], filename="analysis/audio-lib-freq.txt", perm="w+")
#write_val(len(only_libs['env']), "env-only libs")
write_freq_map(only_libs['env'], filename="analysis/env-lib-freq.txt", perm="w+")
#write_val(len(only_libs['visual']), "visual-only libs")
write_freq_map(only_libs['visual'], filename="analysis/visual-lib-freq.txt", perm="w+")

# get overall top 5
all_freq = OrderedDict()
for typ in only_libs:
    for l, ct in only_libs[typ].items():
        all_freq[l] = ct

for l, ct in common_libs.items():
    all_freq[l] = ct

write_freq_map(all_freq, filename="analysis/all-lib-freq.txt", perm="w+")

write_str("", "Top 5 libs by frequency (in % of apps)")
write_list_raw(get_top_5_freq(all_freq, num_apps), STATS_FILE, perm="a+", sort=False)

# get all the unused libs
unused = OrderedDict()
unused['audio'] = read_set("corpus/audio-unused-libs.txt")
unused['env'] = read_set("corpus/env-unused-libs.txt")
unused['multi'] = read_set("corpus/multi-unused-libs.txt")
unused['visual'] = read_set("corpus/visual-unused-libs.txt")

# count the frequency of each unused lib
distinct_unused = OrderedDict()
for cat in unused:
    distinct_unused = count_freq(unused[cat], distinct_unused)

write_list_raw(distinct_unused.keys(), "corpus/all-unused-libs.txt")
write_val(len(distinct_unused), "unused libs")
write_freq_map(distinct_unused, filename="analysis/unused-freq.txt", perm="w+")

write_str("", "Top 5 unused libs by frequency (in % of apps)")
write_list_raw(get_top_5_freq(distinct_unused, num_apps), STATS_FILE, perm="a+", sort=False)
