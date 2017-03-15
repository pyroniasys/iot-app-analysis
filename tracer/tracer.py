import sys, os, gc, inspect
import json
from collections import OrderedDict
from optparse import OptionParser

_caller_cache = dict()
level = 0
tlm = None

last_callers = dict()
last_callees = dict()

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

    if level == len(levels):
        return None

    lvl_dict = levels[lvl_str]

    if level > 1 and lvl_dict.get(caller) == None:
        return None

    else:
        l = []
        for callee in lvl_dict[caller]:
            d = _build_call_graph(level+1, callee)

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
                if exists == False:
                    l.append(d)
        # prune away this branch of the call graph
        lvl_dict[caller] = []
        return {caller: l}

# build the call graph and pretty print it in json
def _collect_call_graph(app_filename):
    global levels

    print("num levels: "+str(len(levels)-1))
    #print(str(levels))
    main = levels["1"]["/Users/marcela/Research/lib-sandboxing/iot-app-analysis/tracer/tracer.py:__main__.runctx"][0]
    #print(main)
    graph = _build_call_graph(2, main)

    tmp = app_filename.split(".")
    app_name = tmp[len(tmp)-1]
    f = open("callgraphs/"+app_name+"_cg", "w")
    f.write(_to_custom_json(graph)+"\n")
    f.close()

def tracer(frame, event, arg):
    global level
    global levels
    global last_callers
    global last_callees
    global tlm

    callee_code = frame.f_code

    lvl_str = str(level)

    if event == "call" or event == "c_call":
        print(lvl_str)

        caller_frame = frame.f_back

        caller_code = caller_frame.f_code

        if tlm == None and level == 1:
            tlm = callee_code

        if event == "c_call":
            # if we're in a c call, the caller of the c function
            # is actually the callee of the last python frame
            caller_code = callee_code

        # get the caller's name
        caller_name = caller_code.co_filename+":"+_get_func_name(caller_code)

        #print(caller_name)

        # this is to make up for any in-line imports because calls
        # to the import lib don't call return, so the level isn't
        # brought back to the level that called the import
        if level > 2 and caller_name == levels["1"]["/Users/marcela/Research/lib-sandboxing/iot-app-analysis/tracer/tracer.py:__main__.runctx"][0]:
            level = 2
            lvl_str = str(level)

        if last_callers.get(lvl_str) == None:
            # this is the first time we enter this level
            last_callers[lvl_str] = caller_name

        if level > 1 and last_callers[str(level-1)] == caller_name:
            caller_name = last_callees[str(level-1)]

        # this is used to map into the levels dict
        if levels.get(lvl_str) == None:
            levels[lvl_str] = OrderedDict()

        # don't include the importlib plumbing in the callgraph
        if "frozen importlib._bootstrap" in caller_name:
            level +=1
            return tracer

        callee_name = ""
        if event == "c_call":
            callee_name = _full_funcname(arg)
        else:
            callee_name = callee_code.co_filename+":"+_get_func_name(callee_code)

        sys.stdout.write(caller_name+" --> "+callee_name+"\n")

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
        #print("ret: "+callee_code.co_name)
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

def test_tracer(frame, event, arg):
    callee = frame.f_code
    if event == "call":
        caller = frame.f_back.f_code
        sys.stdout.write(caller.co_filename+"-->"+callee.co_filename+"\n")
        sys.stdout.write(caller.co_name+"-->"+callee.co_name+"\n")
        return test_tracer
    elif event == "c_call":
        sys.stdout.write(callee.co_name+"-->"+arg.__qualname__+"\n")
        return test_tracer
    return None

# modeled after https://github.com/python/cpython/blob/3.5/Lib/profile.py
# runctx()
def runctx(cmd, globs, locs):
    global tlm
    try:
        sys.setprofile(tracer)
        try:
            exec(cmd, globs, locs)
        finally:
            sys.setprofile(None)
            _collect_call_graph(modname(tlm.co_filename))

    except IOError as err:
        sys.setprofile(None)
        print ("Cannot run file %r because: %s" % (sys.argv[0], err))
        sys.exit(-1)
    except SystemExit:
        pass


# modeled after https://github.com/python/cpython/blob/3.5/Lib/profile.py
def main():
    usage = "tracer.py scriptfile"
    parser = OptionParser(usage=usage)
    parser.allow_interspersed_args = False

    if not sys.argv[1:]:
        parser.print_usage()
        sys.exit(2)

    (options, args) = parser.parse_args()
    sys.argv[:] = args

    if len(args) > 0:
        progname = args[0]
        sys.path.insert(0, os.path.dirname(progname))
        sys.path.insert(0, "../lib-stats/libs")
        with open(progname, 'rb') as fp:
            code = compile(fp.read(), progname, 'exec')
        globs = {
            '__file__': progname,
            '__name__': '__main__',
            '__package__': None,
            '__cached__': None,
        }
        runctx(code, globs, None)
    else:
        parser.print_usage()
    return parser

if __name__ == "__main__":
    main()
