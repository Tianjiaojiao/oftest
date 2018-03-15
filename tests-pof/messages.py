"""These tests fall under Conformance Test-Suite (OF-SWITCH-1.0.0 TestCases).
    Refer Documentation -- Detailed testing methodology 
    <Some of test-cases are directly taken from oftest> """

"Test Suite 2 --> POF Protocol messages"


import logging

import unittest
import random
import time
import os
import copy

from oftest import config
import oftest.controller as controller
import ofp
import oftest.dataplane as dataplane
import oftest.parse as parse
import oftest.base_tests as base_tests

from oftest.testutils import *
from time import sleep
#from FuncUtils import *  for now


class Hello(base_tests.SimpleDataPlane):

    def runTest(self):
        time.sleep(1)

        logging.info("Running Hello test")

        # Send Hello message
        logging.info("Sending Hello...")
        request = ofp.message.hello()
        self.controller.message_send(request)

        # Verify Hello message in response
        logging.info("After handshake is done, switch will send an error msg when receive hello")
        (response, pkt) = self.controller.poll(exp_msg=ofp.POFT_ERROR,
                                               timeout=1)
        self.assertTrue(response is not None,
                        'Switch did not receive error message')
        self.assertTrue(response.err_type == ofp.POFET_BAD_REQUEST, 'error_type is not bad request')
        self.assertTrue(response.code == ofp.POFBRC_BAD_TYPE, 'error_code is not bad type')
        self.assertTrue(response.version == 0x04, 'pof-version field is not 4')

class ErrorMsg(base_tests.SimpleProtocol):
    """
    Verify POFT_ERROR msg is implemented

    When the header in the  request msg
    contains a version field which is not supported by the switch ,
    it generates POFT_ERROR_msg with Type field POFET_BAD_REQUEST
    and code field POFBRC_BAD_VERSION
    """

    def runTest(self):
        time.sleep(1)
        logging.info("Running Error Msg test")

        # Send Echo Request
        logging.info("Sending a Echo request with a version which is not supported by the switch")
        request = ofp.message.echo_request()
        request.version = 0
        self.controller.message_send(request)

        logging.info("Waiting for a POFT_ERROR msg on the control plane...")
        (response, pkt) = self.controller.poll(exp_msg=ofp.POFT_ERROR,
                                               timeout=5)
        self.assertTrue(response is not None,
                        'Switch did not reply with error message')
        self.assertTrue(response.err_type == ofp.POFET_BAD_REQUEST,
                        'Message field type is not POFET_BAD_REQUEST')
        self.assertTrue(response.code == ofp.POFBRC_BAD_VERSION,
                        'Message field code is not POFBRC_BAD_VERSION')


class Echo(base_tests.SimpleProtocol):
    """Test basic echo-reply is implemented
    a)  Send echo-request from the controller side, note echo body is empty.
    b)  Verify switch responds back with echo-reply with same xid """

    def runTest(self):
        time.sleep(1)
        logging.info("Running Echo test")

        logging.info("Sending Echo Request")
        logging.info("Expecting a Echo Reply with version--0x04 and same xid")

        # Send echo_request
        request = ofp.message.echo_request()
        (response, pkt) = self.controller.transact(request)
        self.assertEqual(response.type, ofp.POFT_ECHO_REPLY, 'response is not echo_reply')
        self.assertEqual(request.xid, response.xid,
                         'response xid != request xid')
        self.assertTrue(response.version == 0x04, 'switch openflow-version field is not 0x04')


class FeaturesRequest(base_tests.SimpleProtocol): 

    """Verify Features_Request-Reply is implemented 
    a) Send POFT_FEATURES_REQUEST
    b) Verify POFT_FEATURES_REPLY is received without errors"""

    def runTest(self):
        time.sleep(1)
        logging.info("Running Features_Request test")

        of_ports = config["port_map"].keys()
        of_ports.sort()

        logging.info("Sending Features_Request")
        logging.info("Expecting Features_Reply")

        request = ofp.message.features_request()
        self.controller.message_send(request)

        (response, pkt) = self.controller.poll(exp_msg=ofp.POFT_FEATURES_REPLY,
                                               timeout=2)
        logging.info("receive features reply")

        self.assertTrue(response is not None, 
                        'Did not receive Features Reply')
        self.assertEqual(response.type, ofp.POFT_FEATURES_REPLY, 'Response is not Features_reply')
        self.assertEqual(response.xid, request.xid, 'Transaction id does not match')
        self.assertTrue(response.port_num == 21,
                        'Reply has an error at port_num')
        self.assertTrue(response.table_num == 23,
                        'Reply has an error at table_num')


class ConfigurationRequest(base_tests.SimpleProtocol):

    """Check basic Get Config request is implemented
    a) Send POFT_GET_CONFIG_REQUEST
    b) Verify POFT_GET_CONFIG_REPLY is received without errors"""

    def runTest(self):
        time.sleep(1)
        logging.info("Running Get_Configuration_Request test ")

        of_ports = config["port_map"].keys()
        of_ports.sort()

        logging.info("Sending POFT_GET_CONFIG_REQUEST ")
        logging.info("Expecting POFT_GET_CONFIG_REPLY ")

        request = ofp.message.get_config_request()
        self.controller.message_send(request)

        (reply, pkt) = self.controller.poll(exp_msg=ofp.POFT_GET_CONFIG_REPLY,
                                               timeout=2)
        self.assertTrue(reply is not None, "Failed to get any reply")
        self.assertEqual(reply.type, ofp.POFT_GET_CONFIG_REPLY, 'Response is not Config Reply')
        self.assertEqual(reply.xid, request.xid, 'Transaction id does not match')

        logging.info(repr(pkt))

        (reply1, pkt1) = self.controller.poll(exp_msg=ofp.POFT_RESOURCE_REPORT,
                                               timeout=2)
        self.assertTrue(reply1 is not None, "Failed to get resource report")
        self.assertEqual(reply1.type, ofp.POFT_RESOURCE_REPORT, 'Response is not resource report')

        logging.info(repr(pkt1))
 
        count = 0
        while True:
            (response2, pkt2) = self.controller.poll(exp_msg=ofp.POFT_PORT_STATUS, timeout=2)
            self.assertTrue(response2 is not None,"Did not get get port status")
            count = count+1
            if count == 21:
                break
        self.assertTrue(count == 21, "do not receive 21 port_status")


class SetConfig(base_tests.SimpleProtocol):
    """Verify POFT_SET_CONFIG is implemented"""

    def runTest(self):

        logging.info("Running Set_Config_Request Test")
        #of_ports = config["port_map"].keys()
        #of_ports.sort()

        time.sleep(1)
        # Send get_config_request -- retrive miss_send_len field
        logging.info("Sending Get Config Request ")
        request = ofp.message.get_config_request()
        (reply, pkt) = self.controller.transact(request)
        self.assertTrue(reply is not None, "Failed to get any reply")
        self.assertEqual(reply.type, ofp.POFT_GET_CONFIG_REPLY, 'Response is not Config Reply')

        miss_send_len = 0
        miss_send_len = reply.miss_send_len
        old_flags = 0
        old_flags = reply.flags

        # Send set_config_request --- set a different miss_sen_len field and flag
        logging.info("Sending Set Config Request...")
        req = ofp.message.set_config()

        if miss_send_len < 65400:  # Max miss_send len is 65535
            req.miss_send_len = miss_send_len + 100
            new_miss_send_len = req.miss_send_len
        else:
            req.miss_send_len = miss_send_len - 100
            new_miss_send_len = req.miss_send_len

        if old_flags > 0:
            req.flags = old_flags - 1
            new_flags = req.flags
        else:
            req.flags = old_flags + 1
            new_flags = req.flags

        self.controller.message_send(req)

        # Send get_config_request -- verify change came into effect
        logging.info("Sending Get Config Request...")
        request = ofp.message.get_config_request()

        (rep, pkt) = self.controller.transact(request)
        self.assertTrue(rep is not None, "Failed to get any reply")
        self.assertEqual(rep.type, ofp.POFT_GET_CONFIG_REPLY, 'Response is not Config Reply')
        self.assertEqual(rep.miss_send_len, new_miss_send_len, "miss_send_len configuration parameter could not be set")
        self.assertEqual(rep.flags, new_flags, "frag flags could not be set")


class PacketIn(base_tests.SimpleDataPlane):
    """Test basic packet_in function
    a) Send a simple tcp packet to a dataplane port, without any flow-entry
    b) Verify that a packet_in event is sent to the controller"""

    def runTest(self):
        logging.info("Running Packet_In test")

        of_ports = config["port_map"].keys()
        of_ports.sort()
        ingress_port = of_ports[0]

        logging.info("Sending a Simple tcp packet a dataplane port")
        logging.info("Expecting a packet_in event on the control plane")

        # Send  packet on dataplane port and verify packet_in event gets generated.
        pkt = simple_tcp_packet()
        self.dataplane.send(ingress_port, str(pkt))
        logging.info("Sending packet to dp port " + str(ingress_port) +
                     ", expecting packet_in on control plane")

        verify_packet_in(self, str(pkt), ingress_port, ofp.POFR_NO_MATCH)


class PacketInSizeMiss(base_tests.SimpleDataPlane):
    """ When packet_in is triggered due to a flow table miss,
        verify the data sent in packet_in varies in accordance with the
        miss_send_len field set in POFT_SET_CONFIG"""

    def runTest(self):
        sleep(1)
        logging.info("Running PacketInSizeMiss Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        # Send a set_config_request message
        miss_send_len = [0, 32, 64, 100]

        for bytes in miss_send_len:
            req = ofp.message.set_config()
            req.miss_send_len = bytes
            self.controller.message_send(req)
            sleep(1)

            # Send packet to trigger packet_in event
            pkt = simple_tcp_packet()
            self.dataplane.send(of_ports[0], str(pkt))

            # Verify packet_in generated
            response = verify_packet_in(self, str(pkt), of_ports[0], ofp.POFR_NO_MATCH)

            # Verify buffer_id field and data field
            if response.buffer_id == 0xFFFFFFFF:#ofp_no_buffer
                self.assertTrue(len(response.data) == len(str(pkt)),
                                "Buffer None here but packet_in is not a complete packet")
            elif (bytes == 0):
                self.assertEqual(len(response.data), bytes, "PacketIn Size is not equal to miss_send_len")
            else:
                self.assertTrue(len(response.data) >= bytes, "PacketIn Size is not at least miss_send_len bytes")

class PacketInSizeAction(base_tests.SimpleDataPlane):
    """When the packet is sent because of a "send to controller" action,
        verify the data sent in packet_in varies in accordance with the
        max_len field set in action_output"""

    def runTest(self):

        logging.info("Running PacketInSizeAction Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        # Create a simple tcp packet
        pkt = simple_tcp_packet()

        # Set value and mask
        list = []
        for i in range(16):
            list.append(0x00)
        value = list
        value[0] = 0x06
        mask = copy.deepcopy(list)
        mask[0] = 0xff

        match_table = ofp.match
        match_table.field_id = 0x8000
        match_table.offset = 184 #tcp
        match_table.len = 8

        match_flow = ofp.match_x
        match_flow.field_id = 0x8000
        match_flow.offset = 184 #tcp
        match_flow.len = 8
        match_flow.value = value
        match_flow.mask = mask#em

        # Insert a table
        msg = ofp.message.table_add()
        msg.table_id = 0
        msg.table_type = 0
        msg.match_field_num = 1
        msg.table_name = "first flow table"
        msg.size = 2 #the table could add two entry
        msg.match = []
        msg.match.append(match_table)
        msg.key_len = 0
        for m in msg.match:
            msg.key_len += m.len
        print(msg.key_len)
        self.controller.message_send(msg)
        sleep(1)

        # Insert a flow entry with action --output to controller
        act = ofp.action.output()
        act.portId_type = 0
        act.value = ofp.POFP_CONTROLLER

        ins = ofp.instruction.apply_actions()
        ins.action_num = 1
        ins.actions = []
        ins.actions.append(act)

        request = ofp.message.flow_add()
        request.match = []
        request.match.append(match_flow)
        request.match_field_num = 1
        request.instruction_num = 1
        request.table_id = 0
        request.instructions = []
        request.instructions.append(ins)

        logging.info("Inserting flow....")
        self.controller.message_send(request)
        # Send packet matching the flow
        logging.debug("Sending packet to dp port " + str(of_ports[0]))
        self.dataplane.send(of_ports[0], str(pkt))

        # Verifying packet_in recieved on the control plane
        response = verify_packet_in(self, str(pkt), of_ports[0], ofp.POFR_ACTION)

        # Verify buffer_id field and data field
        if response.buffer_id != 0xFFFFFFFF:
            self.assertTrue(len(response.data) <= bytes, "Packet_in size is greater than max_len field")
        else:
            self.assertTrue(len(response.data) == len(str(pkt)),
                                "Buffer None here but packet_in is not a complete packet")
        sleep(5)
#flow_removed, pofswitch do not supported


class PortStatus(base_tests.SimpleDataPlane):
    """Verify Port Status Messages are sent to the controller
    whenever physical ports are added, modified or deleted"""

    def runTest(self):
        logging.info("Running PortStatusMessage Test")

        # Bring down the port by shutting the interface connected
        try:
            logging.info("Bringing down the interface ..")
            os.system("ifconfig eth1 down")#should to ensure eth1 is up
            #self.dataplane.port_down(of_ports[0]) will report a socket error

            # Verify Port Status message is recieved with reason-- Port Deleted
            logging.info("Verify PortStatus-Down message is recieved on the control plane ")
            (response, raw) = self.controller.poll(ofp.POFT_PORT_STATUS, timeout=15)
            self.assertTrue(response is not None,
                            'Port Status Message not generated')
            self.assertEqual(response.reason, ofp.POFPR_MODIFY, "The reason field of Port Status Message is incorrect")

        # Bring up the port by starting the interface connected
        finally:
            logging.info("Bringing up the interface ...")
            os.system("ifconfig eth1 up")
            #self.dataplane.port_up(of_ports[num])

        # Verify Port Status message is recieved with reason-- Port Added
        logging.info("Verify Port Status Up message is received")
        (response, raw) = self.controller.poll(ofp.POFT_PORT_STATUS, timeout=15)

        self.assertTrue(response is not None,
                        'Port Status Message not generated')
        self.assertEqual(response.reason, ofp.POFPR_MODIFY, "The reason field of Port Status Message is incorrect")
        (response, raw) = self.controller.poll(ofp.POFT_PORT_STATUS, timeout=15)


#resource_report, just used in reply config_request
'''
#pofswitch do not supported
class PacketOut(base_tests.SimpleDataPlane):
    """Test packet out function
    a) Send packet out message for each dataplane port.
    b) Verify the packet appears on the appropriate dataplane port"""

    def runTest(self):

        logging.info("Running Packet_Out test")

        of_ports = config["port_map"].keys()
        of_ports.sort()

        # Clear Switch state
        delete_all_flows(self.controller)

        logging.info("Sending a packet-out for each dataplane port")
        logging.info("Expecting the packet on appropriate dataplane port")

        for dp_port in of_ports:
            for outpkt, opt in [
                (simple_tcp_packet(), "simple TCP packet"),
                (simple_eth_packet(), "simple Ethernet packet"),
                (simple_eth_packet(pktlen=40), "tiny Ethernet packet")]:

                msg = ofp.message.packet_out()
                msg.data = str(outpkt)
                act = ofp.action.output()
                act.port = dp_port
                msg.actions.append(act)
                msg.buffer_id = 0xffffffff

                logging.info("PacketOut to: " + str(dp_port))
                self.controller.message_send(msg)

                exp_pkt_arg = None
                exp_port = None
                if config["relax"]:
                    exp_pkt_arg = outpkt
                    exp_port = dp_port
                (of_port, pkt, pkt_time) = self.dataplane.poll(timeout=2,
                                                               port_number=exp_port,
                                                               exp_pkt=exp_pkt_arg)

                self.assertTrue(pkt is not None, 'Packet not received')
                logging.info("PacketOut: got pkt from " + str(of_port))
                if of_port is not None:
                    self.assertEqual(of_port, dp_port, "Unexpected receive port")
                if not dataplane.match_exp_pkt(outpkt, pkt):
                    logging.debug("Sent %s" % format_packet(outpkt))
                    logging.debug("Resp %s" % format_packet(
                        str(pkt)[:len(str(outpkt))]))
                self.assertEqual(str(outpkt), str(pkt)[:len(str(outpkt))],
                                 'Response packet does not match send packet')


class ModifyStateDelete(base_tests.SimpleProtocol):

    """Check Basic Flow Delete request is implemented
    a) Send POFT_FLOW_MOD, command = POFFC__ADD
    b) Send pof_table_stats request , verify active_count=1 in reply
    c) Send POFT_FLOW_MOD, command = POFFC__DELETE
    c) Send pof_table_stats request , verify active_count=0 in reply"""

    def runTest(self):

        logging.info("Running Modify_State_Delete test")

        of_ports = config["port_map"].keys()
        of_ports.sort()

        #Insert a flow matching on ingress_port 
        (pkt,match) = wildcard_all_except_ingress(self,of_ports)

        #Verify Flow inserted.
        verify_tablestats(self,expect_active=1)

        #Delete the flow 
        nonstrict_delete(self,match)

        # Send Table_Stats_Request and verify flow deleted.
        verify_tablestats(self,expect_active=0)


#group_mod
class GroupModAdd(base_tests.SimpleProtocol):
    """Check basic Group Add request is implemented
    a) Send  POFT_GROUP_MOD , command = POFGC_ADD """

    def runTest(self):
        logging.info("Running Group_Mod_Add test")

        of_ports = config["port_map"].keys()
        of_ports.sort()

        # Clear switch state
        delete_all_groups(self.controller)

        logging.info("Inserting a group")
        logging.info("Expecting active_count=1 in table_stats_reply")

        # Insert a new group entry
        request = ofp.message.group_add()
        request.group_type = 2
        self.controller.message_send(request)

        # Send Table_Stats_Request and verify flow gets inserted.
        verify_tablestats(self, expect_active=1)


class GroupModDelete(base_tests.SimpleProtocol):
    """Check Basic Flow Delete request is implemented
    a) Send POFT_GROUP_MOD, command = POFGC_DELETE
    b)
    c)
    c) """

    def runTest(self):
        logging.info("Running Modify_State_Delete test")

        of_ports = config["port_map"].keys()
        of_ports.sort()

        # Clear switch state
        delete_all_groups(self.controller)

        logging.info("Inserting a flow entry and then deleting it")
        logging.info("Expecting the active_count=0 in table_stats_reply")

        # Insert a new group entry
        request = ofp.message.group_add()
        request.group_type = 2
        self.controller.message_send(request)

        # Verify Flow inserted.
        verify_tablestats(self, expect_active=1)

        # Delete the flow
        request = ofp.message.group_delete()
        request.group_type = 2
        self.controller.message_send(request)

        # Send Table_Stats_Request and verify flow deleted.
        verify_tablestats(self, expect_active=0)


class GroupModModify(base_tests.SimpleDataPlane):
    """Verify basic Flow Modify request is implemented
    a) Send POFT_GROUP_MOD, command = POFGC_MODIFY, Action A
    b)  """

    def runTest(self):
        logging.info("Running Modify_State_Modify test")

        of_ports = config["port_map"].keys()
        of_ports.sort()

        # Clear switch state
        delete_all_groups(self.controller)

        logging.info("Inserting a flow entry and then modifying it")
        logging.info("Expecting the Test Packet to implement the modified action")

        # Insert a flow matching on ingress_port with action A (output to of_port[1])
        (pkt, match) = wildcard_all_except_ingress(self, of_ports)

        # Modify the flow action (output to of_port[2])
        modify_flow_action(self, of_ports, match)

        # Send the Test Packet and verify action implemented is A' (output to of_port[2])
        send_packet(self, pkt, of_ports[0], of_ports[2])


class PortModFlood(base_tests.SimpleDataPlane):
    """ Modify the behavior of physical port using Port Modification Messages
    Change POFPC_NO_FLOOD flag  and verify change takes place with features request """

    def runTest(self):
        logging.info("Running PortModFlood Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        # Retrieve Port Configuration
        logging.info("Sends Features Request and retrieve Port Configuration from reply")
        (hw_addr, port_config, advert) = \
            port_config_get(self.controller, of_ports[0])
        self.assertTrue(port_config is not None, "Did not get port config")

        logging.debug("No flood bit port " + str(of_ports[0]) + " is now " +
                      str(port_config & ofp.POFPC_NO_FLOOD))

        # Modify Port Configuration
        logging.info("Modify Port Configuration using Port Modification Message:POFT_PORT_MOD")
        rv = port_config_set(self.controller, of_ports[0],
                             port_config ^ ofp.POFPC_NO_FLOOD, ofp.POFPC_NO_FLOOD)
        self.assertTrue(rv != -1, "Error sending port mod")
        do_barrier(self.controller)

        # Verify change took place with features request
        logging.info("Verify the change and then set it back")
        (hw_addr, port_config2, advert) = port_config_get(self.controller, of_ports[0])

        logging.debug("No flood bit port " + str(of_ports[0]) + " is now " +
                      str(port_config2 & ofp.POFPC_NO_FLOOD))
        self.assertTrue(port_config2 is not None, "Did not get port config2")
        self.assertTrue(port_config2 & ofp.POFPC_NO_FLOOD !=
                        port_config & ofp.POFPC_NO_FLOOD,
                        "Bit change did not take")
        # Set it back
        rv = port_config_set(self.controller, of_ports[0], port_config,
                             ofp.POFPC_NO_FLOOD)
        self.assertTrue(rv != -1, "Error sending port mod")
        do_barrier(self.controller)


class PortModFwd(base_tests.SimpleDataPlane):
    """
    Modify the behavior of physical port using Port Modification Messages
    Change POFPC_NO_FWD flag and verify change took place with Features Request"""

    def runTest(self):
        logging.info("Running PortModFwd Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        # Retrieve Port Configuration
        logging.info("Sends Features Request and retrieve Port Configuration from reply")
        (hw_addr, port_config, advert) = \
            port_config_get(self.controller, of_ports[0])
        self.assertTrue(port_config is not None, "Did not get port config")
        logging.debug("No flood bit port " + str(of_ports[0]) + " is now " +
                      str(port_config & ofp.POFPC_NO_FWD))

        # Modify Port Configuration
        logging.info("Modify Port Configuration using Port Modification Message:POFT_PORT_MOD")
        rv = port_config_set(self.controller, of_ports[0],
                             port_config ^ ofp.POFPC_NO_FWD, ofp.POFPC_NO_FWD)
        self.assertTrue(rv != -1, "Error sending port mod")
        do_barrier(self.controller)

        # Verify change took place with features request
        logging.info("Verify the change and then set it back")
        (hw_addr, port_config2, advert) = port_config_get(self.controller, of_ports[0])

        logging.debug("No flood bit port " + str(of_ports[0]) + " is now " +
                      str(port_config2 & ofp.POFPC_NO_FWD))

        self.assertTrue(port_config2 is not None, "Did not get port config2")
        self.assertTrue(port_config2 & ofp.POFPC_NO_FWD !=
                        port_config & ofp.POFPC_NO_FWD,
                        "Bit change did not take")
        # Set it back
        rv = port_config_set(self.controller, of_ports[0], port_config,
                             ofp.POFPC_NO_FWD)
        self.assertTrue(rv != -1, "Error sending port mod")
        do_barrier(self.controller)


class PortModPacketIn(base_tests.SimpleDataPlane):
    """
    Modify the behavior of physical port using Port Modification Messages
    Change POFPC_NO_PACKET_IN flag and verify change took place with Features Request"""

    def runTest(self):
        logging.info("Running PortModPacketIn Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        # Retrieve Port Configuration
        logging.info("Sends Features Request and retrieve Port Configuration from reply")
        (hw_addr, port_config, advert) = \
            port_config_get(self.controller, of_ports[0])
        self.assertTrue(port_config is not None, "Did not get port config")
        logging.debug("No flood bit port " + str(of_ports[0]) + " is now " +
                      str(port_config & ofp.POFPC_NO_PACKET_IN))

        # Modify Port Configuration
        logging.info("Modify Port Configuration using Port Modification Message:POFT_PORT_MOD")
        rv = port_config_set(self.controller, of_ports[0],
                             port_config ^ ofp.POFPC_NO_PACKET_IN, ofp.POFPC_NO_PACKET_IN)
        self.assertTrue(rv != -1, "Error sending port mod")
        do_barrier(self.controller)

        # Verify change took place with features request
        logging.info("Verify the change and then set it back")
        (hw_addr, port_config2, advert) = port_config_get(self.controller, of_ports[0])

        logging.debug("No flood bit port " + str(of_ports[0]) + " is now " +
                      str(port_config2 & ofp.POFPC_NO_PACKET_IN))

        self.assertTrue(port_config2 is not None, "Did not get port config2")
        self.assertTrue(port_config2 & ofp.POFPC_NO_PACKET_IN !=
                        port_config & ofp.POFPC_NO_PACKET_IN,
                        "Bit change did not take")
        # Set it back
        rv = port_config_set(self.controller, of_ports[0], port_config,
                             ofp.POFPC_NO_PACKET_IN)
        self.assertTrue(rv != -1, "Error sending port mod")
        do_barrier(self.controller)


#table_mod


#multipart_request & reply, pofswitch do not supported
#pofswitch do not supported
class BarrierRequestReply(base_tests.SimpleProtocol):

    """ Check basic Barrier request is implemented
    a) Send POFT_BARRIER_REQUEST
    c) Verify POFT_BARRIER_REPLY is recieved"""

    def runTest(self):

        logging.info("Running Barrier_Request_Reply test")

        logging.info("Sending Barrier Request")
        logging.info("Expecting a Barrier Reply with same xid")

        #Send Barrier Request
        request = ofp.message.barrier_request()
        (response,pkt) = self.controller.transact(request)
        self.assertEqual(response.type, ofp.POFT_BARRIER_REPLY,'response is not barrier_reply')
        self.assertEqual(request.xid, response.xid,
                         'response xid != request xid')


class QueueConfigReply(base_tests.SimpleProtocol):
    """Verify Queue Configuration Reply message body """

    def runTest(self):
        logging.info("Running QueueConfigRequest")

        of_ports = config["port_map"].keys()
        of_ports.sort()

        logging.info("Sending Queue Config Request ...")
        request = ofp.message.queue_get_config_request()
        request.port = of_ports[0]
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get reply ")
        self.assertTrue(response.type == ofp.POFT_QUEUE_GET_CONFIG_REPLY, "Reply is not Queue Config Reply")

        # Verify Reply Body
        self.assertEqual(response.xid, request.xid, "Transaction Id in reply is not same as request")
        self.assertEqual(response.port, request.port, "Port queried does not match ")
        queues = []
        queues = response.queues
        logging.info("Queues Configured for port " + str(of_ports[0]) + str(queues))


#role request & reply


#get_async_request & reply & set_async

#meter_mod


#counter_mod


#counter_request & reply


#queryall_request & reply


#instruction_block_mod


#slot_config & status
'''





