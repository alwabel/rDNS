#include<cmath>
#include<iostream>
#include<stdint.h>
using std::cout;
using std::endl;
#include<netinet/in.h>
#include<sys/socket.h>
#include <arpa/inet.h>
int main(){ 
    uint64_t limit = pow(2,32)+15;
    uint64_t p = 3;
    struct in_addr ip;
    for(uint64_t i=0;i<limit;i++) {
        ip.s_addr = htonl(p);

        cout << inet_ntoa(ip) << endl;
        p *= 3;
        p %= limit;

    }
    return 0;
    }
