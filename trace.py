import sys, os, gc, inspect
import json
from collections import OrderedDict

_caller_cache = dict()
level = 0
last_caller = ""
last_callee = ""
returned = False

last_callers = dict()

# want to keep track of each level's call dict
levels = OrderedDict()

# unapologetically ripped off from cpython tracer.py
def _function_name(code):
    '''
    filename = code.co_filename
    if filename:
        modulename = modname(filename)
    else:
        modulename = None
    '''
    
    funcname = code.co_name
    clsname = None
    if code in _caller_cache:
        if _caller_cache[code] is not None:
            clsname = _caller_cache[code]
    else:
        _caller_cache[code] = None
            ## use of gc.get_referrers() was suggested by Michael Hudson
            # all functions which refer to this code object
        funcs = [f for f in gc.get_referrers(code)
                 if inspect.isfunction(f)]
            # require len(func) == 1 to avoid ambiguity caused by calls to
            # new.function(): "In the face of ambiguity, refuse the
            # temptation to guess."
        if len(funcs) == 1:
            # add the module name to the funcname
            dicts = [d for d in gc.get_referrers(funcs[0])
                     if isinstance(d, dict)]            
            if len(dicts) == 1:
                classes = [c for c in gc.get_referrers(dicts[0])
                           if hasattr(c, "__bases__")]
                if len(classes) == 1:
                    # ditto for new.classobj()
                    clsname = classes[0].__name__
                    # cache the result - assumption is that new.* is
                    # not called later to disturb this relationship
                    # _caller_cache could be flushed if functions in
                    # the new module get called.
                    _caller_cache[code] = clsname
    if clsname is not None:
        funcname = "%s.%s" % (clsname, funcname)

    return funcname

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

    if level > 0 and lvl_dict.get(caller) == None:
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
                '''
                if callee not in levels[str(level+1)].keys():
                    # this is also for dedup
                    if callee not in g[c]:
                        g[c].append(callee)
                else:
                '''
                d = _build_call_graph(level+1, callee)

                if d == None:
                    if callee not in g[c]:
                        g[c].append(callee)
                else:
                    if d not in g[c]:                    
                        g[c].append(d)  
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
    global levels
    global last_callers
    global last_callee
    global returned

    callee_code = frame.f_code
    callee_filename = callee_code.co_filename

    lvl_str = str(level)
    print(lvl_str)
    
    # we're at the top of the call stack
    if frame.f_back == None:

        if level != 0:
            raise Exception("Bad level: "+lvl_str)
        
        print(str(len(levels)))
        _collect_call_graph(callee_filename)
        return None

    if event == "call" or event == "c_call":
        
        caller_code = frame.f_back.f_code
        caller_filename = caller_code.co_filename
        
        if event == "c_call":
            # if we're in a c call, the caller of the c function
            # is actually the callee of the last python frame
            caller_code = callee_code
        
        #sys.stdout.write(caller_filename+" --> "+callee_filename+"\n")

        caller_name = ""
        if last_callers.get(lvl_str) == None:
            # this is the first time we enter this level
            caller_name = _get_func_name(caller_code)
        else:
            # we're back to this level
            caller_name = last_callers[lvl_str]

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
