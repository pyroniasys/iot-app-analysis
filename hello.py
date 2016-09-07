import sys
import trace

sys.setprofile(trace.tracer)

def hello():
    f = open("test.txt", "w")
    f.write("blah\n")
    f.close()
    print("Hello, world")

hello()

print("Blah")
