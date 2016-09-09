import sys, os, gc, inspect
import json
from collections import OrderedDict

_caller_cache = dict()
level = 0
last_caller = ""
last_callee = ""
returned = False
tlm = None

last_callers = dict()

# want to keep track of each level's call dict
levels = OrderedDict()

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

def _get_func(code):
    #gc.collect()
    funcs = [f for f in gc.get_referrers(code)
             if inspect.isroutine(f)]
    
    func = None
    if len(funcs) > 0:
        func = funcs[0]
        
    return func

def _full_funcname(f):
    f_name = str(f.__module__)+"."+f.__qualname__
    f_name = f_name.replace("None.", "")
    return f_name

def _get_func_name(code):

    f = _get_func(code)

    if f == None:
        return code.co_name
    else:
        return _full_funcname(f)

def _build_call_graph(level, caller):
    lvl_str = str(level)
    global levels

    lvl_dict = levels[lvl_str]

    if level > 1 and lvl_dict.get(caller) == None:
        return None
    
    elif level == len(levels)-1:        
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
                d = _build_call_graph(level+1, callee)

                if d == None:
                    if callee not in g[c]:
                        g[c].append(callee)
                else:
                    if d not in g[c]:                    
                        g[c].append(d)
            # prune away this branch of the call graph
            lvl_dict[c] = []
        return g

# build the call graph and pretty print it in json
def _collect_call_graph(app_filename):
    global levels

    print("num levels: "+str(len(levels)-1))
    graph = _build_call_graph(1, "trace.start_tracer")

    f = open("traces/"+app_filename+"_cg", "w")
    f.write(_to_custom_json(graph))
    f.close()

def tracer(frame, event, arg):
    global level
    global levels
    global last_callers
    global last_callee
    global returned
    global tlm

    callee_code = frame.f_code

    lvl_str = str(level)
    #print(lvl_str)

    if event == "call" or event == "c_call":

        caller_frame = frame.f_back

        #if caller_frame == None:
            # we've reached the top-level module again
            # we don't have a previous frame, so set the code
            # to the cached top-level module code
            #caller_code = tlm
        #else:
        caller_code = caller_frame.f_code

        if tlm == None and level == 0:
            tlm = callee_code
        
        if event == "c_call":
            # if we're in a c call, the caller of the c function
            # is actually the callee of the last python frame
            caller_code = callee_code

        # get the caller's name
        caller_name = _get_func_name(caller_code)
        if last_callers.get(lvl_str) == None:
            # this is the first time we enter this level
            last_callers[lvl_str] = caller_name

        callee_name = ""
        if event == "c_call":
            callee_name = _full_funcname(arg)
        else:
            callee_name = _get_func_name(callee_code)
            
        if level > 0 and last_callers[str(level-1)] == caller_name and returned == False:
            caller_name = last_callee

        #sys.stdout.write(caller_name+" --> "+callee_name+"\n")

        # this is used to map into the levels dict
        if levels.get(lvl_str) == None:
            levels[lvl_str] = OrderedDict()

        # populate the level's call_graph
        lvl_dict = levels[lvl_str]
        if lvl_dict.get(caller_name) == None:
            lvl_dict[caller_name] = []

        lvl_dict[caller_name].append(callee_name)

        level += 1
        last_callee = callee_name
        last_callers[lvl_str] = caller_name
        returned = False
            
        return tracer

    elif event == "return" or event == "c_return":
        returned = True
        level -= 1

    return None

# from:
# https://github.com/kantai/passe-framework-prototype/blob/master/django/analysis/tracer.py
def modname(path):
    """Return a plausible module name for the path."""
    for p in sys.path:
        if path.startswith(p):
            base = path[len(p):]
            if base.startswith("/"):
                base = base[1:]
            name, ext = os.path.splitext(base)
            return name.replace("/",".")    
    base = os.path.basename(path)
    filename, ext = os.path.splitext(base)
    return filename

# adapted from:
# https://github.com/kantai/passe-framework-prototype/blob/master/django/analysis/tracer.py
def start_tracer(callback):
    global tlm
    try:
        sys.setprofile(tracer)
        try:
            return callback()
        finally:
            sys.setprofile(None)
            _collect_call_graph(modname(tlm.co_filename))

    except IOError as err:
        sys.setprofile(None)
        print ("Cannot run file %r because: %s" % (sys.argv[0], err))
        sys.exit(-1)
    except SystemExit:
        pass
