import sys, os, gc, inspect
import json
from collections import OrderedDict

_caller_cache = dict()
cur_caller = ""
level = 0

# want to keep track of each level's call dict
levels = OrderedDict()
levels["0"] = OrderedDict()

def _get_caller_func(caller_code):
    gc.collect()
    er_f = [f for f in gc.get_referrers(caller_code)
            if inspect.isroutine(f)]

    caller = None
    if len(er_f) > 0:
        caller = er_f[0]

    return caller

def _get_callee_func(callee_code):
    gc.collect()
    ee_f = [f for f in gc.get_referrers(callee_code)
            if inspect.isroutine(f)]

    callee = None
    if len(ee_f) > 0:
        callee = ee_f[0]

    return callee

def _print_func_call_relationship(callee, caller):

    caller_name = ""
    if caller != None:
        caller_name = str(caller.__module__)+"."+caller.__qualname__
        caller_name = caller_name.replace("None.", "")

    callee_name = ""
    if callee != None:
        callee_name = str(callee.__module__)+"."+callee.__qualname__
        callee_name = callee_name.replace("None.", "")

    sys.stdout.write(caller_name+" --> "+callee_name+"\n")
    return (caller_name, callee_name)

def _build_call_graph_inner(level, caller):
    global levels
    if level == len(levels)-1:
        return levels[str(level)][caller]

    g = OrderedDict()
    for caller, callees in levels[str(level)].items():
        g[caller] = []
        for callee in callees:
            g[caller].append({callee: _build_call_graph_inner(level+1,callee, )})
    return g

# build the call graph and pretty print it in json
def _collect_call_graph(app_filename):
    global levels

    graph = OrderedDict()
    for c in levels["0"]:
        graph[c] = _build_call_graph_inner(0, c)

    f = open("traces/"+app_filename+"_cg", "w")
    f.write(json.dumps(graph, indent=4, separators=(',', ': ')))
    f.close()

def tracer(frame, event, arg):
    global level
    global cur_caller
    global levels
    
    # get the callee and caller code objects and filenames
    callee_code = frame.f_code
    callee_filename = callee_code.co_filename
    
    caller_frame = frame.f_back
    if caller_frame == None:
        _collect_call_graph(callee_filename)
        return None

    caller_code = caller_frame.f_code
    caller_filename = caller_code.co_filename

    if event == "call" or event == "c_call":
        sys.stdout.write(caller_filename+" --> "+callee_filename+"\n")

        callee = arg
        if event == "call":
            callee = _get_callee_func(callee_code)

        caller = _get_caller_func(caller_code)
            
        if caller == None:
            sys.stdout.write(caller_code.co_name)
            
        (caller_name, callee_name) = _print_func_call_relationship(callee, caller)

        if caller_name == "":
            caller_name = caller_code.co_name
        if callee_name == "":
            callee_name = callee_code.co_name

        # this is used to map into the levels dict
        lvl_str = str(level)
        if levels.get(lvl_str) == None:
            levels[lvl_str] = OrderedDict()

        # populate the level's call_graph
        lvl_dict = levels[lvl_str]
        if lvl_dict.get(caller_name) == None:
            lvl_dict[caller_name] = [callee_name]
        else:
            lvl_dict[caller_name].append(callee_name)
        
        if cur_caller != caller_name:
            cur_caller = caller_name
            
        return tracer

    elif event == "return" or event == "c_return":
        if cur_caller != caller_code.co_name and level > 0:
            cur_caller = caller_code.co_name
            level -= 1

    return None
