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


def InsertTable(controller,field_id,offset,len,table_id,table_type,match_field_num,table_name):

    match_table = ofp.match
    match_table.field_id = field_id
    match_table.offset = offset
    match_table.len = len

    # Insert a table
    msg = ofp.message.table_add()
    msg.table_id = table_id
    msg.table_type = table_type
    msg.match_field_num = 1
    msg.table_name = table_name
    msg.size = 2 #the table could add two entry
    msg.match = []
    msg.match.append(match_table)
    msg.key_len = 0
    for m in msg.match:
         msg.key_len += m.len
    controller.message_send(msg)

def InsertFlow(controller,field_id,offset,len,value,mask,table_id,ins):

    match_flow = ofp.match_x
    match_flow.field_id = field_id
    match_flow.offset = offset #tcp
    match_flow.len = len
    match_flow.value = value
    match_flow.mask = mask#em

    request = ofp.message.flow_add()
    request.match = []
    request.match.append(match_flow)
    request.match_field_num = 1
    request.instruction_num = 1
    request.table_id = table_id
    request.instructions = []
    request.instructions.append(ins)

    controller.message_send(request)

def SetValueMask(valuestr,maskstr):

    list = []
    for i in range(16):
        list.append(0x00)
    value = copy.deepcopy(list)
    mask = copy.deepcopy(list)
    length = len(valuestr)/2
    for i in range(16):
        if i < length:
            value[i] = int(valuestr[2*i:2*i+2],16)
            mask[i] = 0xff
        else:
            value[i] = 0x00
            mask[i] = 0x00
    return value,mask

class GotoTable(base_tests.SimpleDataPlane):

    def runTest(self):
        sleep(1)
        logging.info("Running goto_table Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        # Create a simple tcp packet
        pkt = simple_tcp_packet()

        InsertTable(self.controller,0x0000,96,16,0,0,1,"first flow table")
        sleep(1)
        InsertTable(self.controller,0x0000,184,8,1,0,1,"tcp/udp flow table")
        sleep(1)
        InsertTable(self.controller,0x0000,240,32,2,0,1,"dst_ip flow table")
        sleep(1)

        # Set value and mask
        value1,mask1 = SetValueMask("0800","ffff")
        value2,mask2 = SetValueMask("06","ff")
        value3,mask3 = SetValueMask("c0a80002","ffffffff")

        ins1 = ofp.instruction.goto_table()
        ins1.next_table_id = 1
        ins1.match_field_num = 1
        ins1.packet_offset = 0

        InsertFlow(self.controller,0x0000,96,16,value1,mask1,0,ins1)
        sleep(1)

        ins2 = ofp.instruction.goto_table()
        ins2.next_table_id = 2
        ins2.match_field_num = 1
        ins2.packet_offset = 0

        InsertFlow(self.controller,0x0000,184,8,value2,mask2,1,ins2)
        sleep(1)

        act = ofp.action.output()
        act.portId_type = 0
        act.value = 0x00000011#slot_id = 0x0000,port_id = 0x0011

        ins3 = ofp.instruction.apply_actions()
        ins3.action_num = 1
        ins3.actions = []
        ins3.actions.append(act)

        InsertFlow(self.controller,0x0000,216,32,value3,mask3,2,ins3)
        sleep(1)

        # Send packet matching the flow
        logging.debug("Sending packet to dp port " + str(of_ports[0]))
        self.dataplane.send(of_ports[0], str(pkt))

        # Verifying packet_in recieved on the control plane
        (of_port, pkt_in, pkt_time) = self.dataplane.poll(exp_pkt=pkt)
        self.assertTrue(pkt_in is not None,
                        'Packet is not received')
        self.assertTrue(of_port == 17,
                        'Packet is not received on port ' + str(of_port))


class SetField(base_tests.SimpleDataPlane):

    def runTest(self):
        sleep(1)
        logging.info("Running set_field Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        # Create a simple tcp packet
        pkt = simple_tcp_packet()

        InsertTable(self.controller,0x0000,96,16,0,0,1,"first flow table")
        sleep(1)

        # Set value and mask
        value_field_set,mask_field_set = SetValueMask("ffffffff","ffffffff")
        value,mask = SetValueMask("0800","ffff")

        field_set = ofp.match_x
        field_set.field_id = 0
        field_set.offset = 240
        field_set.len = 32
        field_set.value = value_field_set
        field_set.mask = mask_field_set

        act1 = ofp.action.set_field()
        act1.field_setting = field_set

        act2 = ofp.action.output()
        act2.portId_type = 0
        act2.value = 0x00000011#slot_id = 0x0000,port_id = 0x0011

        ins = ofp.instruction.apply_actions()
        ins.action_num = 2
        ins.actions = []
        ins.actions.append(act1)
        ins.actions.append(act2)

        InsertFlow(self.controller,0x0000,96,16,value,mask,0,ins)
        sleep(1)

        # Send packet matching the flow
        logging.debug("Sending packet to dp port " + str(of_ports[0]))
        self.dataplane.send(of_ports[0], str(pkt))

        # Verifying packet_in recieved on the control plane
        (of_port, pkt_in, pkt_time) = self.dataplane.poll(exp_pkt=pkt)
        self.assertTrue(pkt_in is not None,
                        'Packet is not received')
        self.assertTrue(of_port == 17,
                        'Packet is not received on port ' + str(of_port))
        #self.assertTrue(of_port == 17,
        #                'Packet is not received on port ' + str(of_port))

