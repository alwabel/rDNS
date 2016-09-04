#!/usr/bin/env python
from dns.resolver import Resolver
from dns.resolver import Answer
from dns import reversename
from dns.resolver import *
import dns.rdataclass
import dns.rdatatype
import dns.exception
import socket
class MyResolver(Resolver):
    def query(self,qname):
        rdclass = dns.rdataclass.IN
        #rdtype = "PTR"
        rdtype = dns.rdatatype.PTR
        request = dns.message.make_query(qname,rdtype,rdclass)
        nameservers = self.nameservers[:]
        response = None
        while response is None:
            if len(nameservers) == 0:
                raise NoNameservers
            for ns in nameservers:
                try:
                    response = dns.query.udp(request,ns,5)
                except (socket.error,dns.exception.Timeout):
                    response = None
                    nameservers.remove(ns)
                    continue
                except dns.query.UnexpectedSource:
                    response = None
                    nameservers.remove(ns)
                    continue
                except dns.exception.FormError:
                    nameservers.remove(ns)
                    repsonse = None
                    continue
                rcode = response.rcode()
                if rcode == dns.rcode.YXDOMAIN:
                    raise YXDOMAIN
                if rcode == dns.rcode.NOERROR or rcode == dns.rcode.NXDOMAIN:
                    break
                if rcode != dns.rcode.SERVFAIL:
                    nameservers.remove(ns)
            if not response is None:
                break
        return Answer(qname,rdtype,rdclass,response,True)
if __name__ == "__main__":
    r=MyResolver()
    a=r.query( reversename.from_address("4.2.2.2") ) 
    for b in a:
        print b
#    print r.query("2.2.2.4.in-addr.arpa")
