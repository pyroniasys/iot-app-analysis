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
    #gc.collect()
    er_f = [f for f in gc.get_referrers(caller_code)
            if inspect.isroutine(f)]

    caller = None
    if len(er_f) > 0:
        caller = er_f[0]

    return caller

def _get_callee_func(callee_code):
    #gc.collect()
    ee_f = [f for f in gc.get_referrers(callee_code)
            if inspect.isroutine(f)]

    callee = None
    if len(ee_f) > 0:
        callee = ee_f[0]

    return callee

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
            comma = "\n"
            ret += SPACE * INDENT * (level+1)
            ret += str(k) + ':' + SPACE
            ret += _to_custom_json(v, level + 1)

        ret += NEWLINE + SPACE * INDENT * level + "}"
    elif isinstance(o, str):
        ret += o
    elif isinstance(o, list):
        ret += "[" + ", ".join([_to_custom_json(e, level+1) for e in o]) +"]"
    else:
        raise TypeError("Unknown type '%s' for json serialization" % str(type(o)))
    return ret

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

def _build_call_graph(level, caller):
    lvl_str = str(level)
    global levels

    lvl_dict = levels[lvl_str]

    if level == len(levels)-1:

        # let's dedup the function names
        l = []
        for callee in lvl_dict[caller]:
            if callee not in l:
                l.append(callee)
                
        return {caller: l}
    else:
        g = OrderedDict()
        for c, callees in lvl_dict.items():
            g[c] = []
            for callee in callees:
                if callee not in levels[str(level+1)]:
                    # this is also for dedup
                    if callee not in g[c]:
                        g[c].append(callee)
                else:
                    g[c].append(_build_call_graph(level+1, callee))  
        return g

# build the call graph and pretty print it in json
def _collect_call_graph(app_filename):
    global levels
    
    graph = _build_call_graph(0, "")

    f = open("traces/"+app_filename+"_cg", "w")
    f.write(_to_custom_json(graph))
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
            level += 1
            
        return tracer

    elif event == "return" or event == "c_return":
        if cur_caller != caller_code.co_name and level > 0:
            cur_caller = caller_code.co_name
            level -= 1

    return None
