# -*- coding: utf-8 -*-

"""
    FixedResolver - example resolver which responds with fixed response
                    to all requests
"""

from __future__ import print_function

import copy

from dnslib import RR
from dnslib.server import DNSServer,DNSHandler,BaseResolver,DNSLogger

fixed_zone = """
ns1.burrow.tech. 60 IN A 131.215.172.230
ns2.burrow.tech. 60 IN A 131.215.172.230
test123.burrow.tech. 60 IN TXT 'I am test123.'
bacon.burrow.tech. 60 IN TXT "Bacon ipsum dolor amet frankfurter filet mignon tenderloin, jowl short loin corned beef jerky beef ribs spare ribs. Kevin bresaola venison jowl filet mignon. Turducken pork belly pig ball tip tail, alcatra brisket leberkas tri-tip" "fatback jerky pancetta filet mignon tenderloin. Landjaeger cupim drumstick rump shankle doner cow. Meatball prosciutto tri-tip, doner bresaola landjaeger ball tip andouille pork chop cupim ground round ribeye drumstick pastrami. " "Cow tenderloin picanha prosciutto pancetta, fatback andouille shoulder. Pig drumstick cow, landjaeger short loin chuck beef ribs. Andouille swine leberkas jowl ribeye doner biltong cupim ball tip prosciutto corned beef. T-bone sirloin filet" " mignon tongue alcatra shank pig short ribs pork belly tenderloin ribeye. Beef picanha pork t-bone bacon tail salami fatback frankfurter ribeye doner turducken. Porchetta doner rump short loin turducken tenderloin sausage pork. Tenderloin t-bone" "tri-tip shankle. Tri-tip ground round pork belly, landjaeger ham pancetta bresaola meatball ribeye strip steak pig alcatra. Alcatra sausage tri-tip biltong shoulder bresaola. Shankle swine cow, sausage brisket short loin picanha kielbasa" " turkey strip steak t-bone tongue hamburger. Shank ham hock pork loin, fatback alcatra andouille prosciutto short loin pastrami shankle hamburger. Boudin ham hamburger filet mignon bacon drumstick. Pork chop prosciutto capicola "
"""
wildcard_zone = "whatgoesheredoesntmatter. 60 IN TXT 'Hello world!'"

class FixedResolver(BaseResolver):
    """
        Respond with fixed response to some requests, and wildcard to all others.
    """
    def __init__(self):
        # Parse RRs
        self.fixedrrs = RR.fromZone(fixed_zone)
        self.wildcardrrs = RR.fromZone(wildcard_zone)

    def resolve(self,request,handler):
        reply = request.reply()
        qname = request.q.qname
       
        found = False 
        for rr in self.fixedrrs:
            a = copy.copy(rr)
            if (a.rname == qname):
                found = True
                print("Yay, we found a matching record! " + str(a.rname))
                reply.add_answer(a)
        if (not found):
            print("Darn, we didn't find a matching record. Using wildcard response.")
            assert(len(self.wildcardrrs) == 1)
            a = copy.copy(self.wildcardrrs[0])
            a.rname = qname
            reply.add_answer(a)
        return reply

if __name__ == '__main__':

    import argparse,sys,time

    p = argparse.ArgumentParser(description="Fixed DNS Resolver")
    p.add_argument("--port","-p",type=int,default=53,
                    metavar="<port>",
                    help="Server port (default:53)")
    p.add_argument("--address","-a",default="",
                    metavar="<address>",
                    help="Listen address (default:all)")
    p.add_argument("--udplen","-u",type=int,default=0,
                    metavar="<udplen>",
                    help="Max UDP packet length (default:0)")
    p.add_argument("--tcp",action='store_true',default=False,
                    help="TCP server (default: UDP only)")
    p.add_argument("--log",default="request,reply,truncated,error",
                    help="Log hooks to enable (default: +request,+reply,+truncated,+error,-recv,-send,-data)")
    p.add_argument("--log-prefix",action='store_true',default=False,
                    help="Log prefix (timestamp/handler/resolver) (default: False)")
    args = p.parse_args()
    
    resolver = FixedResolver()
    logger = DNSLogger(args.log,args.log_prefix)

    print("Starting Fixed Resolver (%s:%d) [%s]" % (
                        args.address or "*",
                        args.port,
                        "UDP/TCP" if args.tcp else "UDP"))

    print("Using fixed records:")
    for rr in resolver.fixedrrs:
        print("    | ",rr.toZone().strip(),sep="")
    print("And wildcard record:")
    for rr in resolver.wildcardrrs:
        print("    | ",rr.toZone().strip(),sep="")
    print()

    if args.udplen:
        DNSHandler.udplen = args.udplen

    udp_server = DNSServer(resolver,
                           port=args.port,
                           address=args.address,
                           logger=logger)
    udp_server.start_thread()

    if args.tcp:
        tcp_server = DNSServer(resolver,
                               port=args.port,
                               address=args.address,
                               tcp=True,
                               logger=logger)
        tcp_server.start_thread()

    while udp_server.isAlive():
        time.sleep(1)

