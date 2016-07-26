#!/usr/bin/env python
from dns import resolver
from dns import reversename
import sys
import threading

class reader_wrapper(object):
    def __init__(self,source=sys.stdin):
        self.lock = threading.Lock()
        self.source = source
    def next(self):
        with self.lock:
            return self.source.next()
    def __iter__(self):
        return self
class writer_wrapper(object):
    def __init__(self,dest=sys.stdout):
        self.lock = threading.Lock()
        self.dest = dest
    def write(self,msg):
        with self.lock:
            print >> self.dest, msg
def resolve(ip):
    addr = reversename.from_address(ip)
    result = resolver.query(addr,"PTR")
    names = []
    for r in result:
        names.append( str(r) ) 
    return names

def process(r,w):
    for ip in r:
        ip = ip.strip()
        w.write("{0} ---> {1}".format(ip,resolve(ip)))
        #print "{0} ---> {1}".format(ip,resolve(ip))
def main():
#    for ip in sys.stdin:
#        ip = ip.strip()
#        addr = reversename.from_address(ip)
#        names = resolver.query(addr, "PTR")
#        for name in names:
#            print "{0} -> {1}".format(ip,name)
    r = reader_wrapper()
    w = writer_wrapper()

    MAX_THREADS = 10
    t = []
    for i in range(0,MAX_THREADS):
        d = threading.Thread(target=process,args=(r,w,))
        t.append(d)
        d.start()

    for i in t:
        i.join()
if __name__ == "__main__":
    main()
