import sys, os, gc, inspect

_caller_cache = dict()

def modname(path):
    """Return a plausible module name for the patch."""
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

# unapologetically ripped off from cpython tracer.py
def file_module_function_of(code):
    filename = code.co_filename
    if filename:
        modulename = modname(filename)
    else:
        modulename = None
        
    funcname = code.co_name
    clsname = None
    function = None
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

    return filename, modulename, funcname, function

def test_tracer(frame, event, arg):
    if event == "call":
        call_to_file, call_to_mod, call_to_func, to_func = file_module_function_of(frame.f_code)
        call_from_file, call_from_mod, call_from_func, from_func = file_module_function_of(frame.f_back.f_code)
        sys.stdout.write(call_from_file+"-->"+call_to_file+"\n")
        sys.stdout.write(call_from_mod+"-->"+call_to_mod+"\n")
        sys.stdout.write(call_from_func+"-->"+call_to_func+"\n")
        return test_tracer
    elif event == "c_call":
        sys.stdout.write("function:"+arg.__qualname__+"\n")
        return test_tracer
    return None

def _print_func_call_relationship(callee, caller):
    sys.stdout.write(str(caller.__module__)+"."+caller.__qualname__+" --> "+str(callee.__module__)+"."+callee.__qualname__+"\n")

def test_tracer2(frame, event, arg):
    # get the callee and caller code objects and filenames
    callee_code = frame.f_code
    callee_filename = callee_code.co_filename
    caller_code = frame.f_back.f_code
    caller_filename = caller_code.co_filename

    # get the callee and caller function objects
    gc.collect()
    ee_f = [f for f in gc.get_referrers(callee_code)
            if inspect.isroutine(f)]
    er_f = [f for f in gc.get_referrers(caller_code)
            if inspect.isroutine(f)]

    if event == "call":
        sys.stdout.write(caller_filename+" --> "+callee_filename+"\n")

        callee = ee_f[0]
        
        caller = None
        if len(er_f) > 0:
            caller = er_f[0]
            _print_func_call_relationship(callee, caller)
        else:
            sys.stdout.write(caller_code.co_name+" --> "+str(callee.__module__)+"."+callee.__qualname__+"\n")
        args = callee_code.co_varnames[:callee_code.co_argcount]
        vals = frame.f_locals
        for a in args:
            sys.stdout.write(a+"="+str(vals[a])+"\n")
        return test_tracer2
    elif event == "c_call":
        sys.stdout.write("C: "+caller_filename+" --> "+callee_filename+"\n")

        sys.stdout.write("C: ")
        caller = None
        if len(er_f) > 0:
            caller = er_f[0]
            _print_func_call_relationship(arg, caller)
        else:
            sys.stdout.write(caller_code.co_name+" --> "+str(arg.__module__)+"."+arg.__qualname__+"\n")

        args = callee_code.co_varnames[:callee_code.co_argcount]
        vals = frame.f_locals
        for a in args:
            sys.stdout.write(a+"="+str(vals[a])+"\n")
        return test_tracer2
    elif event == "return":
        ret = arg
        if arg == None:
            ret = "None"
        sys.stdout.write(callee_code.co_name+" => "+ret+"\n")
        return test_tracer2
    elif event == "c_return":
        ret = arg
        if arg == None:
            ret = "None"
        sys.stdout.write("C: "+callee_code.co_name+" => "+str(ret)+"\n")
        return test_tracer2
    return None
    
    

