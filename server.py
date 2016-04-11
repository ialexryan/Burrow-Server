from __future__ import print_function

import copy
import json
import uuid

from dnslib import RR
from dnslib.label import DNSLabel
from dnslib.server import DNSServer, DNSHandler, BaseResolver, DNSLogger

fixed_zone = """
burrow.tech. 60 IN TXT 'Go away!!'
ns1.burrow.tech. 60 IN A 131.215.172.230
ns2.burrow.tech. 60 IN A 131.215.172.230
constant.test.burrow.tech. 60 IN TXT 'I am the constant record.'
bacon.test.burrow.tech. 60 IN TXT "Bacon ipsum dolor amet frankfurter filet mignon tenderloin, jowl short loin corned beef jerky beef ribs spare ribs. Kevin bresaola venison jowl filet mignon. Turducken pork belly pig ball tip tail, alcatra brisket leberkas tri-tip " "fatback jerky pancetta filet mignon tenderloin. Landjaeger cupim drumstick rump shankle doner cow. Meatball prosciutto tri-tip, doner bresaola landjaeger ball tip andouille pork chop cupim ground round ribeye drumstick pastrami. " "Cow tenderloin picanha prosciutto pancetta, fatback andouille shoulder. Pig drumstick cow, landjaeger short loin chuck beef ribs. Andouille swine leberkas jowl ribeye doner biltong cupim ball tip prosciutto corned beef. T-bone sirloin filet" " mignon tongue alcatra shank pig short ribs pork belly tenderloin ribeye. Beef picanha pork t-bone bacon tail salami fatback frankfurter ribeye doner turducken. Porchetta doner rump short loin turducken tenderloin sausage pork. Tenderloin t-bone " "tri-tip shankle. Tri-tip ground round pork belly, landjaeger ham pancetta bresaola meatball ribeye strip steak pig alcatra. Alcatra sausage tri-tip biltong shoulder bresaola. Shankle swine cow, sausage brisket short loin picanha kielbasa" " turkey strip steak t-bone tongue hamburger. Shank ham hock pork loin, fatback alcatra andouille prosciutto short loin pastrami shankle hamburger. Boudin ham hamburger filet mignon bacon drumstick. Pork chop prosciutto capicola"
babies.test.burrow.tech. 60 IN TXT "Hello world 1"
babies.test.burrow.tech. 60 IN TXT "Hello world 2"
babies.test.burrow.tech. 60 IN TXT "Hello world 3"
babies.test.burrow.tech. 60 IN TXT "Hello world 4"
babies.test.burrow.tech. 60 IN TXT "Hello world 5"
babies.test.burrow.tech. 60 IN TXT "Hello world 6"
babies.test.burrow.tech. 60 IN TXT "Hello world 7"
babies.test.burrow.tech. 60 IN TXT "Hello world 8"
babies.test.burrow.tech. 60 IN TXT "Hello world 9"

"""

def get_subdomain(fqdn):
    assert(isinstance(fqdn, DNSLabel))
    assert(fqdn.matchSuffix("burrow.tech"))
    return fqdn.stripSuffix("burrow.tech")

def dict_to_attributes(d):
    # Implement the standard way of representing attributes
    # in TXT records, see RFC 1464
    # Essentially turns {a: b, c: d} into ["a=b","c=d"]
    output = []
    for (key, value) in d.iteritems():
        output.append(str(key) + "=" + str(value))
    return output

def generate_TXT_zone_line(host, text):
    assert(host.endswith(".burrow.tech."))
    # Split the text into 250-char substrings if necessary
    split_text = [text[i:i+250] for i in range(0, len(text), 250)]
    prepared_text = '"' + '" "'.join(split_text) + '"\n'
    zone = host + " 60 IN TXT " + prepared_text
    return zone
def generate_TXT_zone(host, text_list):
    output = ""
    for t in text_list:
       output += generate_TXT_zone_line(host, t)
    return output 

class FixedResolver(BaseResolver):
    """
        Respond with fixed response to some requests, and wildcard to all others.
    """
    def __init__(self):
        # Parse RRs
        self.fixedrrs = RR.fromZone(fixed_zone)
        self.active_transmissions = {}

    def resolve(self,request,handler):
        reply = request.reply()
        qname = request.q.qname
       
        found_fixed_rr = False
        for rr in self.fixedrrs:
            a = copy.copy(rr)
            if (a.rname == qname):
                found_fixed_rr = True
                print("Found a fixed record for " + str(a.rname))
                reply.add_answer(a)
        if (not found_fixed_rr):
            zone = ""
            sub = get_subdomain(qname)
            if (sub.matchSuffix("begin")):
                transmission_id = uuid.uuid4().hex[-8:]
                self.active_transmissions[transmission_id] = ""
                print("Active transmissions are: " + str(self.active_transmissions))
                response_dict = {'success': True, 'transmission_id': transmission_id}
                zone = generate_TXT_zone(str(qname), dict_to_attributes(response_dict))
            elif (sub.matchSuffix("end")):
                transmission_to_end = sub.stripSuffix("end").label[-1]
                try:
                    del self.active_transmissions[transmission_to_end]
                    print("Active transmissions are: " + str(self.active_transmissions))
                    zone = generate_TXT_zone(str(qname), dict_to_attributes({'success': True}))
                except KeyError:
                    print("ERROR: tried to end a transmission that doesn't exist.")
                    zone = generate_TXT_zone(str(qname), dict_to_attributes({'success': False}))
            elif (sub.matchSuffix("continue")):
                transmission_to_continue = sub.stripSuffix("continue").label[-1]
                data = str(sub.stripSuffix(transmission_to_continue + ".continue")).strip(".")
                try:
                    self.active_transmissions[transmission_to_continue] += data
                    print("Active transmissions are: " + str(self.active_transmissions))
                    zone = generate_TXT_zone(str(qname), dict_to_attributes({'success': True}))
                except KeyError:
                    print("ERROR: tried to continue a transmission that doesn't exist.")
                    zone = generate_TXT_zone(str(qname), dict_to_attributes({'success': False}))
            else:
                response_text = "You are " + str(sub)
                zone = generate_TXT_zone_line(str(qname), response_text)
            print("We generated zone:\n" + zone)
            rrs = RR.fromZone(zone)
            rr = rrs[0]
            for rr in rrs:
                reply.add_answer(rr)

        return reply

if __name__ == '__main__':

    import argparse,sys,time

    p = argparse.ArgumentParser(description="Burrow DNS Resolver")
    p.add_argument("--port","-p",type=int,default=53,
                    metavar="<port>",
                    help="Server port (default:53)")
    p.add_argument("--address","-a",default="",
                    metavar="<address>",
                    help="Listen address (default:all)")
    p.add_argument("--udplen","-u",type=int,default=0,
                    metavar="<udplen>",
                    help="Max UDP packet length (default:0)")
    p.add_argument("--notcp",action='store_true',default=False,
                    help="UDP server only (default: UDP and TCP)")
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
                        "UDP" if args.notcp else "UDP/TCP"))

    print("Using fixed records:")
    for rr in resolver.fixedrrs:
        print("    | ",rr.toZone().strip(),sep="")
    print()

    if args.udplen:
        DNSHandler.udplen = args.udplen

    udp_server = DNSServer(resolver,
                           port=args.port,
                           address=args.address,
                           logger=logger)
    udp_server.start_thread()

    if not args.notcp:
        tcp_server = DNSServer(resolver,
                               port=args.port,
                               address=args.address,
                               tcp=True,
                               logger=logger)
        tcp_server.start_thread()

    while udp_server.isAlive():
        time.sleep(1)

