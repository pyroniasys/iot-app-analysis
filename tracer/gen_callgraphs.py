# Given a set of apps under a certain category,
# this executes them while running a tracing function (tracer/tracer.py)
# which collects the callgraph of the app

import subprocess
import time
import sys
import os
import signal

from collections import OrderedDict

import tracer

INDENT = 2
SPACE = " "
NEWLINE = "\n"

# custom JSON serializer for printing small lists and dictionaries
# Source: http://stackoverflow.com/questions/21866774/pretty-print-json-dumps
def _to_custom_json(o, level=0):
    ret = ""
    if isinstance(o, dict):
        ret += "{" + NEWLINE
        comma = ""
        for k,v in o.items():
            ret += comma
            comma = ","+NEWLINE
            ret += SPACE * INDENT * (level+1)
            ret += str(k) + ':' + SPACE
            ret += _to_custom_json(v, level + 1)

        ret += NEWLINE + SPACE * INDENT * level + "}"
    elif isinstance(o, str):
        ret += o
    elif isinstance(o, list):
        if len(o) == 0:
            ret += "[]"
        elif len(o) == 1 and isinstance(o[0], str):
            ret += "[ " + o[0] + " ]"
        else:
            ret += "["+NEWLINE + (SPACE * INDENT * level)
            comma = ", "+NEWLINE+ (SPACE * INDENT * level)
            ret += comma.join([_to_custom_json(e, level+1) for e in o])
            ret += NEWLINE + SPACE * INDENT * level + "]"
    else:
        raise TypeError("Unknown type '%s' for json serialization" % str(type(o)))
    return ret

def _build_call_graph(level, caller, levels):
    lvl_str = str(level)

    if level == len(levels):
        return None

    lvl_dict = levels[lvl_str]

    if level > 1 and lvl_dict.get(caller) == None:
        return None

    else:
        l = []
        for callee in lvl_dict[caller]:
            d = _build_call_graph(level+1, callee, levels)

            if d == None:
                if callee not in l:
                    l.append(callee)
            else:
                # dedup the dict if we already have a dict with
                # the same callee in the list for this caller
                # need this more tedious check bc we're pruning away
                # branches of the call graph
                exists = False
                for i in l:
                    if isinstance(i, dict):
                        if i.get(callee) != None:
                            exists = True
                            break
                if not exists:
                    # cool, so we don't have a dict for this callee
                    # but we don't want importlib calls to pollute the callgraph
                    # so replace calls to importlib with their children's calls
                    # except for the entry into importlib
                    if callee.startswith("<frozen importlib.") and callee != "<frozen importlib._bootstrap>:_frozen_importlib._find_and_load":
                        # ugh, have to dedup the children, too
                        for i in d[callee]:
                            if isinstance(i, dict):
                                l.append(i)
                            elif isinstance(i, str):
                                if i not in l:
                                    l.append(i)
                    else:
                        l.append(d)
        # prune away this branch of the call graph
        lvl_dict[caller] = []
        return {caller: l}

# build the call graph and pretty print it in json
def collect_call_graph(curdir, app_filename, levels):
    #print("num levels: "+str(len(levels)-1))
    #print(str(levels))
    main = levels["1"][curdir+"/tracer.py:tracer._runctx"][0]
    #print(main)
    graph = _build_call_graph(2, main, levels)

    tmp = app_filename.split(".")
    if app_filename.endswith(".py"):
        app_name = tmp[len(tmp)-2]
    else:
        app_name = tmp[len(tmp)-1]
    f = open(curdir+"/callgraphs/"+app_name+"_cg", "w")
    f.write(_to_custom_json(graph)+"\n")
    f.close()

# pass in the category: visual, audio or env
cat = sys.argv[1]

# get the tracer path in order to pass the right path to the
# callgraph generator
tracer_path = sys.argv[2]

# expect apps to be located in apps/cat/
app_path = "../apps/"+cat+"-py3"

# meh, convert everything to python3.5 to normalize the analysis
os.system("2to3 --output-dir="+app_path+" -W -n ../apps/"+cat)

# let's get a list of apps we want to analyze
app_list = os.listdir(app_path)

apps = []
for a in app_list:
    if not a.startswith('.'):
        apps.append(a)

# for now only collect the callgraph for those apps
for a in apps:
    if a.endswith(".py"):
        app = app_path+"/"+a
    else:
        app = app_path+"/"+a+"/"+a+".py"
    # now run the callgraph generator
    levels = tracer.start_tracer(tracer_path, app)

    # generate the callgraph
    collect_call_graph(tracer_path, a, levels)

# cleanup: remove the converted apps
os.system("rm -rf "+app_path)
