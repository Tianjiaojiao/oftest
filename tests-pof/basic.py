"""
Basic protocol and dataplane test cases

It is recommended that these definitions be kept in their own
namespace as different groups of tests will likely define 
similar identifiers.

Current Assumptions:

  The switch is actively attempting to contact the controller at the address
indicated in oftest.config.

"""

import time
import sys
import logging

import unittest
import random

from oftest import config
import oftest.controller as controller
import oftest.dataplane as dataplane
import oftest.base_tests as base_tests
import ofp

import oftest.illegal_message as illegal_message

from oftest.testutils import *

TEST_VID_DEFAULT = 2

@group('smoke')
class Echo(base_tests.SimpleProtocol):
    """
    Test echo response
    """
    def runTest(self):
        request = ofp.message.echo_request()
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get echo reply")
        self.assertEqual(response.type, ofp.POFT_ECHO_REPLY,
                         'response is not echo_reply')
        self.assertEqual(request.xid, response.xid,
                         'response xid != request xid')


@group('smoke')
class PacketIn(base_tests.SimpleDataPlane):
    """
    Test packet in function

    Send a packet to each dataplane port and verify that a packet
    in message is received from the controller for each
    """
    def runTest(self):
        # Construct packet to send to dataplane
        # Send packet to dataplane, once to each port
        # Poll controller with expect message type packet in

        #delete_all_flows(self.controller)
        #do_barrier(self.controller)

        vid = test_param_get('vid', default=TEST_VID_DEFAULT)

        for of_port in config["port_map"].keys():
            for pkt, pt in [
                (simple_tcp_packet(), "simple TCP packet"),
                #(simple_tcp_packet(dl_vlan_enable=True,vlan_vid=vid,pktlen=108),
                #"simple tagged TCP packet"),
                (simple_eth_packet(), "simple Ethernet packet"),
                (simple_eth_packet(pktlen=40), "tiny Ethernet packet")]:

                logging.info("PKT IN test with %s, port %s" % (pt, of_port))
                self.dataplane.send(of_port, str(pkt))
                verify_packet_in(self, str(pkt), of_port, ofp.POFR_NO_MATCH)

@group('smoke')
class PacketInBroadcastCheck(base_tests.SimpleDataPlane):
    """
    Check if bcast pkts leak when no flows are present

    Clear the flow table
    Send in a broadcast pkt
    Look for the packet on other dataplane ports.
    """

    def runTest(self):
        # Need at least two ports
        self.assertTrue(len(config["port_map"]) > 1, "Too few ports for test")

        #delete_all_flows(self.controller)
        #do_barrier(self.controller)

        of_ports = config["port_map"].keys()
        d_port = of_ports[0]
        pkt = simple_eth_packet(eth_dst='ff:ff:ff:ff:ff:ff')

        logging.info("BCast Leak Test, send to port %s" % d_port)
        self.dataplane.send(d_port, str(pkt))

        (of_port, pkt_in, pkt_time) = self.dataplane.poll(exp_pkt=pkt)
        self.assertTrue(pkt_in is None,
                        'BCast packet received on port ' + str(of_port))

#pofswitch do not support packet_out

@group('smoke')
class FlowMod(base_tests.SimpleProtocol):
    """
    Insert a flow

    Simple verification of a flow mod transaction
    """

    def runTest(self):
        logging.info("Running " + str(self))

        add_first_table(self.controller)

        request = ofp.message.flow_add()
        self.controller.message_send(request)

        # poll for error message
        (response, raw) = self.controller.poll(ofp.POFT_ERROR, timeout=3)
        if response:
            if response.err_type == ofp.POFET_FLOW_MOD_FAILED:
                logging.info("Received error message with flow mod failed code")
                self.assertTrue(False,"flow mod failed and received error msg witch flow_mod_failed")
            else:
                self.assertTrue(False,"flow mod failed and did not receive correct error msg")

@group('smoke')
class PortMod(base_tests.SimpleProtocol):

    def runTest(self):
        logging.info("Running " + str(self))
        for of_port, ifname in config["port_map"].items(): # Grab first port
            break

        mod = ofp.message.port_mod()
        mod.desc.port_no = of_port
        self.controller.message_send(mod)

        # poll for error message
        (response, raw) = self.controller.poll(ofp.POFT_ERROR, timeout=3)
        if response:
            if response.err_type == ofp.POFET_PORT_MOD_FAILED:
                logging.info("Received error message with port mod failed code")
                self.assertTrue(False,"port mod failed and received error msg witch port_mod_failed")
            else:
                self.assertTrue(False,"port mod failed and did not receive correct error msg")


@group('smoke')
class BadMessage(base_tests.SimpleProtocol):
    """
    Send a message with a bad type and verify an error is returned
    """

    def runTest(self):
        logging.info("Running " + str(self))
        request = illegal_message.illegal_message_type()

        reply, pkt = self.controller.transact(request)
        logging.info(repr(pkt))
        self.assertTrue(reply is not None, "Did not get response to bad req")
        self.assertTrue(reply.type == ofp.POFT_ERROR,
                        "reply not an error message")
        logging.info(reply.err_type)
        self.assertTrue(reply.err_type == ofp.POFET_BAD_REQUEST,
                        "reply error type is not bad request")
        self.assertTrue(reply.code == ofp.POFBRC_BAD_TYPE,
                        "reply error code is not bad type")

@group('smoke')
class TableMod(base_tests.SimpleProtocol):
    """
    Simple table mod (add)

    """
    def runTest(self):

        time.sleep(1)

        logging.info("Running "+ str(self))

        # Add a flow table
        add_first_table(self.controller)

        logging.info("Adding a flow table")

        # poll for error message
        (response, raw) = self.controller.poll(ofp.POFT_ERROR, timeout=3)
        if response:
            if response.err_type == ofp.POFET_TABLE_MOD_FAILED:
                logging.info("Received error message with table mod failed code")
                self.assertTrue(False,"table mod failed and received error msg witch table_mod_failed")
            else:
                self.assertTrue(False,"table mod failed and did not receive correct error msg")

if __name__ == "__main__":
    print "Please run through oft script:  ./oft --test_spec=basic"
