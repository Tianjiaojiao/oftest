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


class Output(base_tests.SimpleDataPlane):
    """When the packet is sent because of a "send to controller" action,
        verify the data sent in packet_in varies in accordance with the
        max_len field set in action_output"""

    def runTest(self):

        logging.info("Running output Test")
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
        match_table.field_id = 0x0000
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
        sleep(2)
        self.controller.message_send(msg)

        # Insert a flow entry with instruction:apply_action--action:output
        act = ofp.action.output()
        act.portId_type = 0
        act.value = 0x00000011#slot_id = 0x0000,port_id = 0x0011

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
        (of_port, pkt_in, pkt_time) = self.dataplane.poll(exp_pkt=pkt)
        self.assertTrue(pkt_in is not None,
                        'Packet id not received')
        self.assertTrue(of_port == 17,
                        'Packet is not received on port ' + str(of_port))

