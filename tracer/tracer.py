import sys, os, gc, inspect
from collections import OrderedDict

_caller_cache = dict()
level = 0
curdir = ""

last_callers = dict()
last_callees = dict()

# want to keep track of each level's call dict
levels = OrderedDict()

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

def tracer(frame, event, arg):
    global level
    global levels
    global last_callers
    global last_callees
    global curdir

    callee_code = frame.f_code

    lvl_str = str(level)

    if event == "call" or event == "c_call":
        #print(lvl_str)

        caller_frame = frame.f_back

        caller_code = caller_frame.f_code

        if event == "c_call":
            # if we're in a c call, the caller of the c function
            # is actually the callee of the last python frame
            caller_code = callee_code

        # get the caller's name
        caller_name = caller_code.co_filename+":"+_get_func_name(caller_code)

        # this is to make up for any in-line imports because calls
        # to the import lib don't call return, so the level isn't
        # brought back to the level that called the import
        if level > 2 and caller_name == levels["1"][curdir+"/tracer.py:tracer._runctx"][0]:
            level = 2
            lvl_str = str(level)

        if last_callers.get(lvl_str) == None:
            # this is the first time we enter this level
            last_callers[lvl_str] = caller_name

        if level > 1 and last_callers[str(level-1)] == caller_name:
            caller_name = last_callees[str(level-1)]

        callee_name = ""
        if event == "c_call":
            callee_name = _full_funcname(arg)
        else:
            callee_name = callee_code.co_filename+":"+_get_func_name(callee_code)

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
        last_callees[lvl_str] = callee_name
        last_callers[lvl_str] = caller_name

        return tracer

    elif event == "return" or event == "c_return":
        level -= 1

    return None

# taken from
# https://github.com/kantai/passe-framework-prototype/blob/master/django/analysis/tracer.py
def _modname(path):
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

# adapted from
# https://github.com/kantai/passe-framework-prototype/blob/master/django/analysis/tracer.py
# https://github.com/python/cpython/blob/3.5/Lib/profile.py
def _runctx(cmd, globs, locs):
    try:
        sys.setprofile(tracer)
        try:
            exec(cmd, globs, locs)
        except Exception as err:
            print("Encountered error: "+str(err))
        finally:
            sys.setprofile(None)
    except SystemExit:
        pass

# adapted from https://github.com/python/cpython/blob/3.5/Lib/profile.py
def start_tracer(tracer_dir, scriptfile):
    global curdir
    global levels

    sys.path.insert(0, os.path.dirname(scriptfile))
    sys.path.insert(0, "../libs")
    with open(scriptfile, 'rb') as fp:
        code = compile(fp.read(), scriptfile, 'exec')
        globs = {
            '__file__': scriptfile,
            '__name__': '__main__',
            '__package__': None,
            '__cached__': None,
        }
    curdir = tracer_dir
    _runctx(code, globs, None)

    return levels
