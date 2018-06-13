#!/usr/bin/env python
#
# Create veth pairs
#

import os
import time
from subprocess import Popen,PIPE,call,check_call
from optparse import OptionParser

parser = OptionParser(version="%prog 0.1")
parser.set_defaults(port_count=4)
parser.set_defaults(pof_dir="../pofswitch-1.4.0.015")
parser.set_defaults(port=6633)
parser.add_option("-n", "--port_count", type="int",
                  help="Number of veth pairs to create")
parser.add_option("-o", "--pof_dir", help="POF root directory for host")
parser.add_option("-p", "--port", type="int",
                  help="Port for POF to listen on")
parser.add_option("-N", "--no_wait", action="store_true",
                  help="Do not wait 2 seconds to start daemons")
(options, args) = parser.parse_args()

call(["/sbin/modprobe", "veth"])
for idx in range(0, options.port_count):
    veth = "veth%d" % (idx*2)
    veth_peer = "veth%d" % (idx*2+1)
    print "Creating veth pair " + str(idx) + ": " + veth + " with " + veth_peer
    call(["/sbin/ip", "link", "add", "name", veth, "type", "veth",
          "peer", "name", veth_peer])

for idx in range(0, 2 * options.port_count):
    cmd = ["/sbin/ifconfig", 
           "veth" + str(idx), 
           "192.168.1" + str(idx) + ".1", 
           "netmask", 
           "255.255.255.0"]
    print "Cmd: " + str(cmd)
    call(cmd)

veths = "veth0"
for idx in range(1, options.port_count):
    veths += ",veth" + str(2 * idx)

"""
#ofd = options.of_dir + "/udatapath/ofdatapath"
#ofp = options.of_dir + "/secchan/ofprotocol"
#sudo pofswitch will start datapath, see pofswitch-1.4.0.015 README
pof = options.pof_dir + "/pofswitch"
 
try:
    check_call(["ls", pof])
except:
    print "Could not find daemon: " + pof
    sys.exit(1)

if not options.no_wait:
    print "Starting pofswitch in 2 seconds; ^C to quit"
    time.sleep(2)
else:
    print "Starting pofswitch; ^C to quit"

#ofd_op = Popen([ofd, "-i", veths, "punix:/tmp/ofd"])
#print "Started ofdatapath on IFs " + veths + " with pid " + str(ofd_op.pid)

call([pof, "-P", "-i 127.0.0.1", "-p"+ str(options.port)])#if add other parameters, pofswitch will exit after operation

#ofd_op.kill()
"""




