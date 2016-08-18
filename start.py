#!/usr/bin/env python
import urllib2
import ssl
import os
import tempfile
import sys
from subprocess import PIPE,Popen
import argparse
import math
from multiprocessing import Process
from resolve import start
def download_alloc(filename):
    url = "https://www.iana.org/assignments/ipv4-address-space/ipv4-address-space.csv"
    gcontext = ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    response=urllib2.urlopen(url,context=gcontext)
    with open(filename,"w") as f:
        f.write( response.read() )
def read_alloc(filename):
    blocks = []
    with open(filename,"r") as f:
        for line in f:
            line = line.strip()
            fields=  line.split(',')
            if fields[-2].lower() == "allocated":
#                blocks.extend( gen_ip(fields[0]) )
                blocks.append( fields[0] )
    return blocks

def gen_ip(block):
    ip,net = block.split('/')
    ip=int(ip)<<(32-int(net))
    IPs = []
    for i in range(0, 2** (32 - int(net))):
        IPs.append( ip+i )
    IPs = map(int_to_ip , IPs)
    return IPs
def int_to_ip(ip):
    ip = int(ip)
    result = "{0}.{1}.{2}.{3}".format(ip>>24, (ip & 0x00FF0000) >> 16, ( ip & 0x0000FF00) >> 8 , ip & 0xFF)
    return result
                
def main():
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-n","--parts",help="Number of partitions",default=1,type=int)
    parser.add_argument("--prefix",help="output file's prefix",default="rand")
    parser.add_argument("--outputdir",help="output dir",default="/tmp")
    args = parser.parse_args()
    parts = args.parts
    outputdir = args.outputdir
    prefix = args.prefix
    filename = "ipv4-address-space.csv"
    if not os.path.isfile( filename ):
        download_alloc(filename)
    blocks = read_alloc(filename)

    f= tempfile.NamedTemporaryFile(delete=False,dir=args.outputdir) 
    size = 0
    for i,b in enumerate(blocks):
        IPs = gen_ip(b) 
        size += len(IPs)
        f.write('\n'.join(IPs))
    fname =  f.name
    f.close()
    FNULL=open(os.devnull,"w")
    cmd = ['sort','-R',fname] 
    p = Popen( ' '.join(cmd),stdout=PIPE,stderr=FNULL,shell=True)
    part_size = math.ceil(size*1.0/args.parts)
    index = 0
    f = open(os.path.join(args.outputdir,"{0}-in-{1}".format(args.prefix,index) ) ,"w")
    i = 0
    for ip in p.stdout:
        i+=1
        if i>part_size:
            f.close()
            #open new file
            index+=1
            i = 0
            f = open(os.path.join(args.outputdir,"{0}-in-{1}".format(args.prefix,index) ) ,"w")
        
        ip = ip.strip()
        print >> f, ip

    if f is not None: f.close()
    os.remove(fname)

    process = []
    for i in range(0,args.parts):
        filename=os.path.join(args.outputdir,"{0}-in-{1}".format(args.prefix,i)) 
        output = os.path.join(args.outputdir,"{0}-out-{1}".format(args.prefix,i)) 

        p = Process(target=start,args=(filename,output,))
        p.start()
        process.append( p )
    for p in process:
        p.join()

    for i in range(0,args.parts):
        filename=os.path.join(args.outputdir,"{0}-in-{1}".format(args.prefix,i))
        os.remove(filename) 

    cmd = ['sort','-k1,1n','*'] 
    p = Popen( ' '.join(cmd),stdout=PIPE,stderr=FNULL,shell=True)
    with open(os.path.join(args.outputdir,args.prefix),"w") as f:
        for line in p.stdout:
            line = line.strip()
            print >>f, line
    for i in range(0,args.parts):
        filename=os.path.join(args.outputdir,"{0}-out-{1}".format(args.prefix,i))
        os.remove(filename) 


if __name__ == "__main__":
    main()
