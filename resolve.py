#!/usr/bin/env python
from dns import resolver
from dns import reversename
import dns
import sys
import threading
import time
import bz2
class reader_wrapper(object):
    def __init__(self,source=sys.stdin):
        self.lock = threading.Lock()
        if type(source) == type(''):
            self.source = open(source,"r")
        else: self.source = source
    def next(self):
        with self.lock:
            return self.source.next()
    def __iter__(self):
        return self

class writer_wrapper(object):
    def __init__(self,dest=sys.stdout):
        self.lock = threading.Lock()
        if type(dest) == type(''):
            if dest.endswith(".bz2"): self.dest = bz2.BZ2File(dest,"w")
            else:self.dest = open(dest,"w")
        else: self.dest = dest
    def write(self,msg):
        with self.lock:
            print >> self.dest, msg
def int_to_ip(ip):
    a,b,c,d = ip.split('.')
    a = int(a)
    b = int(b)
    c = int(c)
    d = int(d)
    return (a<<24) | (b << 16) | (c<<8) | d

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
        start = time.time()
        #IPs = resolve(ip)
        IPs = ['test']
        end = time.time()
        w.write("{0}\t{1}\t{2}\t{3}\t{4}".format(int_to_ip(ip),ip,','.join(IPs),end-start,start) )
        #print "{0} ---> {1}".format(ip,resolve(ip))

def start(input=sys.stdin,output=sys.stdout):
    r = reader_wrapper(input)
    w = writer_wrapper(output)

    MAX_THREADS = 10
    t = []
    for i in range(0,MAX_THREADS):
        d = threading.Thread(target=process,args=(r,w,))
        t.append(d)
        d.start()

    for i in t:
        i.join()

def main():
    start()
if __name__ == "__main__":
    main()
