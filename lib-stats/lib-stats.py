# Gather statistics about the collected IoT apps

import sys
import os
from collections import OrderedDict

from util import *

# remove an existing stats file since we'll want to override it
if os.path.isfile("stats.txt"):
    os.remove("stats.txt")

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

distinct_libs = get_distinct(libs)
num_libs = len(distinct_libs)

write_val(num_libs, "libs")
write_list_raw(distinct_libs, "all-libs.txt")

for cat in libs:
    dist = get_distinct_cat(cat, libs)
    write_val(len(dist), cat+" libs")

# get all common libs
common_libs = get_common(libs)

write_val(len(common_libs), "common libs")
write_freq_map(common_libs)

write_list_raw(common_libs.keys(), "common-libs.txt")

'''

# get all unique sensor libs
only_sens_libs = get_unique("sens", libs)

write_val(len(only_sens_libs['vis']), "visual-only sensor libs")
write_freq_map(only_sens_libs['vis'])
write_val(len(only_sens_libs['audio']), "audio-only sensor libs")
write_freq_map(only_sens_libs['audio'])
write_val(len(only_sens_libs['env']), "env-only sensor libs")
write_freq_map(only_sens_libs['env'])

# get all unique processing libs
only_proc_libs = get_unique("proc", libs)
write_val(len(only_proc_libs['vis']), "visual-only data processing libs")
write_freq_map(only_proc_libs['vis'])
write_val(len(only_proc_libs['audio']), "audio-only data processing libs")
write_freq_map(only_proc_libs['audio'])
write_val(len(only_proc_libs['env']), "env-only data processing libs")
write_freq_map(only_proc_libs['env'])

# get all unique networking libs
only_net_libs = get_unique("net", libs)
write_val(len(only_net_libs['vis']), "visual-only networking libs")
write_freq_map(only_net_libs['vis'])
write_val(len(only_net_libs['audio']), "audio-only networking libs")
write_freq_map(only_net_libs['audio'])
write_val(len(only_net_libs['env']), "env-only networking libs")
write_freq_map(only_net_libs['env'])

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
