import sys
import trace
from inspect import signature

def hello():
    f = open("test.txt", "w")
    f.write("blah\n")
    f.close()
    print("Hello, world")

def start_trace():
    try:
        sys.settrace(trace.test_tracer2)
        try:
            hello()
        finally:
            sys.settrace(None)
            print("Done")
    except IOError as err:
        sys.settrace(None)
        print("Error %s" % err)
        sys.exit(-1)
    except SystemExit:
        pass

sys.setprofile(trace.test_tracer3)
hello()

