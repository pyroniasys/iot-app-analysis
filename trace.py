import sys, os, gc, inspect
from collections import OrderedDict

_caller_cache = dict()
cur_caller = ""
level = 0
call_graph = OrderedDict()
parent = call_graph

def _print_func_call_relationship(callee, caller):

    caller_name = ""
    if caller != None:
        caller_name = str(caller.__module__)+"."+caller.__qualname__

    caller_name = caller_name.replace("None.", "")

    callee_name = str(callee.__module__)+"."+callee.__qualname__
    callee_name = callee_name.replace("None.", "")

    sys.stdout.write(caller_name+" --> "+callee_name+"\n")
    return caller_name

def test_tracer2(frame, event, arg):
    global level
    global cur_caller
    # get the callee and caller code objects and filenames
    callee_code = frame.f_code
    callee_filename = callee_code.co_filename
    caller_frame = frame.f_back
    if caller_frame == None:
        return None

    caller_code = caller_frame.f_code
    caller_filename = caller_code.co_filename

    # get the callee and caller function objects
    gc.collect()
    ee_f = [f for f in gc.get_referrers(callee_code)
            if inspect.isroutine(f)]
    er_f = [f for f in gc.get_referrers(caller_code)
            if inspect.isroutine(f)]

    caller = None
    if len(er_f) > 0:
        caller = er_f[0]

    if event == "call":
        sys.stdout.write(caller_filename+" --> "+callee_filename+"\n")

        callee = ee_f[0]
        
        if caller == None:
            sys.stdout.write(caller_code.co_name)
        caller_name = _print_func_call_relationship(callee, caller)

        if cur_caller != caller_name:
            cur_caller = caller_name
            level += 1

        return test_tracer2
    elif event == "c_call":
        sys.stdout.write("C: "+caller_filename+" --> "+callee_filename+"\n")

        sys.stdout.write("C: ")

        if caller == None:
            sys.stdout.write(caller_code.co_name)

        caller_name = _print_func_call_relationship(arg, caller)

        if cur_caller != caller_name:
            cur_caller = caller_name
            level += 1

        return test_tracer2
    elif event == "return":
        if cur_caller != caller_code.co_name and level > 0:
            cur_caller = caller_code.co_name
            level -= 1
    elif event == "c_return":
        if cur_caller != caller_code.co_name and level > 0:
            cur_caller = caller_code.co_name
            level -= 1

    return None
    
    

