#!/usr/bin/env python
import urllib2
import ssl
import os
import tempfile
import sys
from subprocess import PIPE,Popen
import argparse
import math
from multiprocessing import Process,JoinableQueue
from resolve import start
import bz2
import logging

logging.basicConfig(format='%(asctime)s %(levelname)s:%(message)s', level=logging.WARNING)

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
            if fields[-2].lower() == "allocated" or fields[-2].lower() == "reserved":
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



def sort_output(parts,prefix,outputdir):
    FNULL=open(os.devnull,"w")

    #cmd = ['bzcat']
    cmd = ['cat']
    for i in range(0,parts):
        filename=os.path.join(outputdir,"{0}-out-{1}.bz2".format(prefix,i))
        cmd.append(filename)
    p1 = Popen(' '.join(cmd),stdout=PIPE,shell=True)
    cmd = ['sort','-k1,1n'] 

    p2 = Popen( ' '.join(cmd),stdout=PIPE,stderr=FNULL,stdin=p1.stdout,shell=True)
    with bz2.BZ2File(os.path.join(outputdir,prefix+".bz2"),"w") as f:
        for line in p2.stdout:
            line = line.strip()
            line = '\t'.join(line.split('\t')[1:])
            print >>f, line

def get_randomip(white_list):
    for i in xrange(0,2**32+15):
        if i == 0: p = 1
        elif i == 1: p =3
        else: p = p*3
        #x = (3**i) % (2**32+15)
        x = p % (2**32+15)
        ip = int_to_ip(x)
        if "{0}/8".format(ip.split('.')[0]) in white_list:
            yield ip

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
        print "Downloading %s" % filename
        download_alloc(filename)

    print "Parsing %s" % filename

    white_list = read_alloc(filename)
    process = []
    tasks = JoinableQueue()

    for i in range(0,args.parts):
        filename=os.path.join(args.outputdir,"{0}-in-{1}".format(args.prefix,i))
        output = os.path.join(args.outputdir,"{0}-out-{1}.bz2".format(args.prefix,i))
        p = Process(target=start,args=(tasks,output,))
        p.start()
        process.append( p )

#    for p in process:
#        p.join()
    for i,ip in enumerate( get_randomip(white_list)):
        tasks.put(ip)
    for i in range(0,args.parts):
        tasks.put(None)
    tasks.join()
    print "sorting outputs"
    sort_output(args.parts,args.prefix,args.outputdir)
    for i in range(0,args.parts):
        filename=os.path.join(args.outputdir,"{0}-out-{1}.bz2".format(args.prefix,i))
        #os.remove(filename) 

if __name__ == "__main__":
    main()
