from collections import OrderedDict

DEBUG = False

def debug(msg):
    if DEBUG:
        print(str(msg))

# remove duplicate entries from a list
def remove_dups(l):
    return sorted(list(set(l)))

def sort_freq_map(m):
    d = OrderedDict(sorted(m.items(), key=lambda kv: (-kv[1], kv[0])))
    return d

def map2list(m):
    l = []
    for k, v in m.items():
        l.append(k+": %.1f" % v)
    return l

def map2list_int(m):
    l = []
    for k, v in m.items():
        l.append(k+": "+str(v))
    return l

def install_lib_pip(lib):
    no_pip = []
    try:
        subprocess.check_output(["sudo", "pip", "install", "-U", lib])
    except subprocess.CalledProcessError as e:
        # the lib name is not in the pip repo, is inconsistent
        # with the name in the pip repo
        print("[collect_callgraphs] Could not download "+lib)
        no_pip.append(lib)

    return no_pip
