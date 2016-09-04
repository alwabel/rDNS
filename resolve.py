#!/usr/bin/env python
import sys
import threading
import time
import bz2
from multiprocessing import JoinableQueue
from myresolver import *
try:
    import dns
    from dns import resolver
    from dns import reversename
except ImportError:
    print >>sys.stderr, "install dns package: apt-get install python-dnspython"
    sys.exit(-1)
class reader_wrapper(object):
    def __init__(self,source=sys.stdin):
        self.lock = threading.Lock()
        self._done = False
        #self.pending_tasks = {}
        if type(source) == type(''):
            self.source = open(source,"r")
        else: self.source = source
    def next(self):
        with self.lock:
            if self._done == True: raise StopIteration 
            if type(self.source) == type(JoinableQueue()):
                next_task = self.source.get()
                #self.pending_tasks[next_task] = 0
                if next_task != None:return next_task
                else: 
                    self._done = True
                    raise StopIteration
            else: return self.source.next()
    def __iter__(self):
        return self
    def done(self,task=None):
        with self.lock:
            if type(self.source) == type(JoinableQueue()):
                #if task is not None: del self.pending_tasks[task]
                self.source.task_done()     
import os
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
    def close(self):
        with self.lock:
            self.dest.close() 
def int_to_ip(ip):
    a,b,c,d = ip.split('.')
    a = int(a)
    b = int(b)
    c = int(c)
    d = int(d)
    return (a<<24) | (b << 16) | (c<<8) | d

R = None
def get_resolver():
    global R
    if R is None:
        R = MyResolver()
    return R
def resolve(ip):
    addr = reversename.from_address(ip)
    try:
        #result = resolver.query(addr,"PTR")
        result=get_resolver().query(addr)
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
        IPs = resolve(ip)
        #IPs = ['test']
        end = time.time()
        try:
            w.write("{0}\t{1}\t{2}\t{3}\t{4}".format(int_to_ip(ip),ip,','.join(IPs),end-start,start) )
        except:
            print "ip = {}".format(ip)
        #print "{0} ---> {1}".format(ip,resolve(ip))
        r.done()
def start(input=sys.stdin,output=sys.stdout):
    r = reader_wrapper(input)
    w = writer_wrapper(output)

    MAX_THREADS = 150
    t = []
    for i in range(0,MAX_THREADS):
        d = threading.Thread(target=process,args=(r,w,))
        t.append(d)
        d.start()

    for i in t:
        i.join()
    w.close()
    r.done()
def main():
    start()
if __name__ == "__main__":
    main()
