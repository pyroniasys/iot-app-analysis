import sys, os, gc, inspect, traceback
from collections import OrderedDict

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

class Tracer:
    '''IoT app analysis tracer class.

    Tracer is used to generate the callgraph of the given application.
    '''

    def __init__(self, tracer_dir, out, fs, app=""):
        # context for this tracer
        self.curdir = tracer_dir
        self.files = fs
        self.app_filename = ""
        self.top_app = app
        self.name = self.curdir+"/tracer.py:tracer.Tracer._runctx"
        self.callgraph_out = out

        # data needed to build the per-level callgraph
        self._caller_cache = dict()
        self.level = 0
        self.last_callers = dict()
        self.last_callees = dict()
        # this helps us detect if we're in an infinite loop
        self.call_freq = dict()
        self.inf_thresh = 20

        # want to keep track of each level's call dict
        # this contains a per-level representation of the callgraph
        # that needs to be built using _build_call_graph
        self.levels = OrderedDict()
        self.main = ""

    def _build_call_graph(self, level, caller):
        lvl_str = str(level)

        # this check is needed so python doesn't hate itself
        # when it execs this when Tracer.collect_call_graph() is imported
        if self.level == 0 or level == len(self.levels):
            return None

        lvl_dict = self.levels[lvl_str]

        if level > 1 and lvl_dict.get(caller) == None:
            return None

        else:
            l = []
            for callee in lvl_dict[caller]:
                d = self._build_call_graph(level+1, callee)

                if d == None:
                    # let's ignore even single calls to the import lib
                    if callee not in l and not callee.startswith("<frozen importlib."):
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

    # taken from
    # https://github.com/kantai/passe-framework-prototype/blob/master/django/analysis/tracer.py
    def _modname(self, path):
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

    # build the call graph and pretty print it in json
    def collect_call_graph(self):
        #print("num levels: "+str(len(levels)-1))
        #print(str(levels))
        #print(main)
        graph = self._build_call_graph(2, self.main)

        if graph != None:
            app_name = self._modname(self.app_filename).split(".")
            if self.top_app == "":
                cg_out = self.callgraph_out+"/"+app_name[len(app_name)-1]+"_cg"
            else:
                cg_out = self.callgraph_out+"/"+self.top_app+"-"+app_name[len(app_name)-1]+"_cg"
            f = open(cg_out, "w")
            f.write(_to_custom_json(graph)+"\n")
            f.close()

    ''' Helper functions to get the right function
    name for each traced code object.
    '''

    # adapted from
    # https://github.com/kantai/passe-framework-prototype/blob/master/django/analysis/tracer.py
    def _get_func(self, code):
        #gc.collect()
        funcs = [f for f in gc.get_referrers(code)
                 if inspect.isroutine(f)]

        func = None
        if len(funcs) > 0:
            func = funcs[0]

        return func

    def _full_funcname(self, f):
        f_name = str(f.__module__)+"."+f.__qualname__
        f_name = f_name.replace("None.", "")
        return f_name

    def _get_func_name(self, code):
        f = self._get_func(code)

        if f == None:
            return code.co_name
        else:
            return self._full_funcname(f)

    def tracer(self, frame, event, arg):
        callee_code = frame.f_code

        lvl_str = str(self.level)

        if event == "call" or event == "c_call":
            #print(lvl_str)

            caller_frame = frame.f_back

            caller_code = caller_frame.f_code

            if event == "c_call":
                # if we're in a c call, the caller of the c function
                # is actually the callee of the last python frame
                caller_code = callee_code

            # get the caller's name
            caller_name = caller_code.co_filename+":"+self._get_func_name(caller_code)

            # this is to make up for any in-line imports because calls
            # to the import lib don't call return, so the level isn't
            # brought back to the level that called the import
            if self.level > 2 and \
               caller_name == self.levels["1"][self.name][0]:
                self.level = 2
                lvl_str = str(self.level)

            if self.last_callers.get(lvl_str) == None:
                # this is the first time we enter this level
                self.last_callers[lvl_str] = caller_name

            if self.level > 1 and self.last_callers[str(self.level-1)] == caller_name:
                caller_name = self.last_callees[str(self.level-1)]

            callee_name = ""
            if event == "c_call":
                callee_name = self._full_funcname(arg)
            else:
                callee_name = callee_code.co_filename+":"+self._get_func_name(callee_code)

            # let's check here if we're in an infinite loop
            # the caller would be the app.py:<module>
            # let's not include imports, since apps may have a bunch
            if self.level == 2 and caller_name == self.levels["1"][self.name][0] and \
               callee_name != "<frozen importlib._bootstrap>:_frozen_importlib._find_and_load":
                if self.call_freq.get(callee_name) == None:
                    self.call_freq[callee_name] = 1
                else:
                    self.call_freq[callee_name] += 1

                if self.call_freq[callee_name] > self.inf_thresh:
                    raise RuntimeError("We're in an infinite loop, so stop tracing")

            #sys.stdout.write(caller_name+" --> "+callee_name+"\n")

            # this is used to map into the levels dict
            if self.levels.get(lvl_str) == None:
                self.levels[lvl_str] = OrderedDict()

            # populate the level's call_graph
            lvl_dict = self.levels[lvl_str]
            if lvl_dict.get(caller_name) == None:
                lvl_dict[caller_name] = []

            lvl_dict[caller_name].append(callee_name)

            if self.level == 1 and self.main == "":
                self.main = self.levels["1"][self.name][0]

            self.level += 1
            self.last_callees[lvl_str] = callee_name
            self.last_callers[lvl_str] = caller_name

            return self.tracer

        elif event == "return" or event == "c_return":
            self.level -= 1

        return None

    # adapted from
    # https://github.com/kantai/passe-framework-prototype/blob/master/django/analysis/tracer.py
    # https://github.com/python/cpython/blob/3.5/Lib/profile.py
    def _runctx(self, cmd, globs, locs):
        try:
            sys.setprofile(self.tracer)
            try:
                exec(cmd, globs, locs)
            except Exception:
                print("Encountered error: "+traceback.format_exc())
            finally:
                sys.setprofile(None)
        except SystemExit:
            pass

    # adapted from https://github.com/python/cpython/blob/3.5/Lib/profile.py
    def start_tracer(self):
        sys.path.insert(0, "../libs")
        for a in self.files:
            self.app_filename = a
            sys.path.insert(0, os.path.dirname(self.app_filename))
            with open(a, 'rb') as fp:
                code = compile(fp.read(), self.app_filename, 'exec')
            globs = {
                '__file__': self.app_filename,
                '__name__': '__main__',
                '__package__': None,
                '__cached__': None,
            }
            self._runctx(code, globs, None)
