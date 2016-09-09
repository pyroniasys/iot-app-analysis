import sys
import trace

def hello():
    f = open("test.txt", "w")
    f.write("blah\n")
    f.close()
    print("Hello, world")

trace.start_tracer(hello)
