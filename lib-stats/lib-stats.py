# Gather statistics about the collected IoT apps

import sys
import os

from util import *

# remove an existing stats file since we'll want to override it
if os.path.isfile("stats.txt"):
    os.remove("stats.txt")

# get all the apps
apps = dict()
apps['visual'] = read_set("visual-apps.txt")
apps['audio'] = read_set("audio-apps.txt")
apps['env'] = read_set("env-apps.txt")

# get total number of distinct apps
distinct_apps = get_distinct(apps)

num_apps = len(distinct_apps)

write_val(num_apps, "apps")

# get all the libs
libs = dict()
libs['vis-sens'] = read_set("visual-sensor-libs.txt")
libs['audio-sens'] = read_set("audio-sensor-libs.txt")
libs['env-sens'] = read_set("env-sensor-libs.txt")
libs['vis-proc'] = read_set("visual-proc-libs.txt")
libs['audio-proc'] = read_set("audio-proc-libs.txt")
libs['env-proc'] = read_set("env-proc-libs.txt")
libs['vis-net'] = read_set("visual-net-libs.txt")
libs['audio-net'] = read_set("audio-net-libs.txt")
libs['env-net'] = read_set("env-net-libs.txt")

distinct_libs = get_distinct(libs)
num_libs = len(distinct_libs)

write_val(num_libs, "libs")

# get all the native lib calls
native_calls = dict()

for cat, l in libs.items():
    for i in l:
        if is_native(i):
            lib = get_lib_name(i)
            if native_calls.get(lib) == None:
                native_calls[lib] = 1
            else:
                native_calls[lib] += 1

write_val(len(native_calls), "native calls")

write_freq_map(native_calls)
