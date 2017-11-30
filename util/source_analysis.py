import re
import os
import os.path

from util.util import debug

def is_code_line(l, is_long_comment):
    if l.startswith("#"):
        if l.startswith("#define") or l.startswith("#ifdef") or l.startswith("#ifndef") or l.startswith("#endif"):
            # this is a macro, so don't treat like a comment!!
            return True, is_long_comment
        else:
            # this is likely to be a single-line python comment
            # we might have a comment within a comment, so need to return
            # the current long_comment status
            return False, is_long_comment
    elif l.startswith ("//") or l.endswith("*/") or ((l.endswith("'''") or l.endswith('"""')) and is_long_comment):
        return False, False
    elif l.startswith("/*"):
        return False, True
    elif l.startswith("'''") or l.startswith('"""') or l.startswith('r"""'):
        # third cond covers exception in stackless/Lib/os.py
        if not (l == "'''" or l == '"""') and (l.endswith("'''") or l.endswith('"""')):
            # we get here if it's actually a single-line comment
            # that uses the multiline symbols
            return False, False
        return False, not is_long_comment
    return True, is_long_comment

# determines whether a line of code makes a call to an external binary
def is_ext_bin_call(l, with_cmd=False):
    if "os.system" in l or "os.spawn" in l or "os.exec" in l or "os.popen" in l or "subprocess.call" in l or "subprocess.Popen" in l or "subprocess.run" in l or "subprocess.check_output" in l or "Popen(" in l or "call([" in l:
        return True
    if with_cmd:
        if "cmd = " in l or "command = " in l:
            return True
    return False

# determines whether a line of code loads a shared library via ctypes
def is_load_shared_lib(l):
    if "CDLL(" in l or "LoadLibrary(" in l or "dlopen(" in l:
        return True
    return False

# determines whether a line of code makes a longjmp
def is_longjmp(l):
    if "setjmp(" in l or "longjmp(" in l:
        return True
    return False

# opens a source file and returns the actual lines of code
def read_source(src):
    f = open(src, "r")

    try:
        lines = f.readlines()
    except UnicodeError as e:
        f.close()
        return None

    f.close()
    code_lines = []
    is_long_comment = False
    for l in lines:
        clean = l.strip()
        # first let's check if it's a line of code
        is_code, is_multiline = is_code_line(clean, is_long_comment)
        if not is_code:
            is_long_comment = is_multiline
        if is_code and not is_long_comment:
            code_lines.append(clean)

    return code_lines

# collect all the native calls so proc collection is only about
# parsing those lines
def scan_source_ext_bin(src, with_cmd=False):
    lines = read_source(src)
    if lines is None:
        return []

    # these are the calls to native code that we've observed
    nats = []
    nextLn = ""
    for l in lines:
        if is_ext_bin_call(l, with_cmd):
            debug("Found call to ext binary in code: "+l)
            # let's make sure the actual command isn't actually
            # on the next line
            if ")" not in l:
                nextLn = l
            else:
                nats.append(l)
        elif nextLn != "":
            nats.append(nextLn+l)
            nextLn = ""
    return nats

# collect all the shared lib loads so proc collection is only about
# parsing those lines
def scan_source_ctypes(src):
    lines = read_source(src)
    if lines is None:
        return []

    # these are the calls to native code that we've observed
    hybs = []
    for l in lines:
        if is_load_shared_lib(l):
            debug("Found shared lib load in code: "+l)
            hybs.append(l)
    return hybs

# collect all instances of setjmp/longjmp in c sources
def scan_source_longjmp(src):
    jmps = []
    lines = read_source(src)
    if lines is None:
        return []

    for l in lines:
        if is_longjmp(l):
            debug("Found longjmp in code: "+l)
            jmps.append(l)
    return jmps

# scans a source file for file system resource accesses
def scan_source_fs_resource(src):
    lines = read_source(src)
    if lines is None:
        return None

    fs_rsrcs = [] # these are all the lines with file paths
    for l in lines:
        if "print(" in l or "printf(" in l:
            continue
        m = re.search("[\'\"](/(dev|usr|etc|proc|sys|tmp|bin|opt|home|System|Users|Library)(/[^\s/]+)+(\.\w+)*)[\'\"]", l)
        if m:
            print(l+": "+m.group(0))
            fs_rsrcs.append(m.group(0))
    return fs_rsrcs

import ctypes.util

# extracts the shared lib loaded by ctypes
def extract_ctypes_shlib(line):

    if line.endswith(".so"):
        return line

    st_idx = line.find('(')
    end_idx = line.find(')')

    # extract the potential shared lib
    shlib_raw = line[st_idx+1:end_idx]
    shlib_raw = shlib_raw.split(',')[0]
    shlib_raw = shlib_raw.strip("'")
    shlib_raw = shlib_raw.strip('"')

    if 'ctypes.util' in shlib_raw:
        # we have a call to ctypes.util.find_lib()
        # we'll want to execute that call to get the actual lib
        l_idx = shlib_raw.find('(')
        lib_name = shlib_raw[l_idx+1:]
        lib_name = lib_name.strip("'")
        shlib = ctypes.util.find_library(lib_name)
        if shlib == None:
            return lib_name
        else:
            return shlib
    else:
        return shlib_raw

# searches for all native source files
def search_c_source(path, lib, is_ctypes=False):
    c = []
    j = []
    for dirpath, dirnames, filenames in os.walk(path):
        for filename in filenames:
            if (filename.endswith(".c") or filename.endswith(".h") or filename.endswith(".cpp") or filename.endswith(".hpp") or filename.endswith(".so")):
                debug("Found C source: "+filename)
                if is_ctypes and filename.endswith(".so"):
                    c.append(filename)
                else:
                    if filename.startswith(lib) or filename.startswith("_"+lib):
                        c.append(filename)
                    if not filename.endswith(".so"):
                        if len(scan_source_longjmp(os.path.join(dirpath, filename))) > 0:
                            debug("Found longjmp")
                            j.append(filename)
    return c, j

def search_shared_libs(path, lib):
    shlibs = []
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            f_hierarch = f.split("/")
            filename = f_hierarch[len(f_hierarch)-1] # the actual filename is the last element
            if filename.startswith(lib+".") and filename.endswith(".so"):
                debug("Found shared lib: "+filename)
                shlibs.append(filename)
    return shlibs
