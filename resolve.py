#!/usr/bin/env python
from dns import resolver
from dns import reversename
import dns
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
    try:
        result = resolver.query(addr,"PTR")
        names = []
        for r in result:
            names.append( str(r)[:-1] ) 
    except dns.resolver.NXDOMAIN:
        return ["NXDOMAIN"]
    except dns.resolver.NoNameservers:
        return ["NoNameservers"]
    except dns.resolver.Timeout:
        return ["Timeout"]
    except dns.resolver.NoAnswer:
        return ["NoAnswer"]
    except Exception as e:
        print >> sys.stderr,"Exception {0}={1}={2}={3}".format(ip,str(e),type(e),e)
        return [str(e)]
    return names

def process(r,w):
    for ip in r:
        ip = ip.strip()
        w.write("{0}\t{1}".format(ip,','.join(resolve(ip))))
        #print "{0} ---> {1}".format(ip,resolve(ip))
def main():
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
