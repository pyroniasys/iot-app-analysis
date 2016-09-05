import sys
import trace
sys.setprofile(trace.test_tracer2)

def hello():
    f = open("test.txt", "w")
    f.write("blah\n")
    f.close()
    print("Hello, world")

hello()

