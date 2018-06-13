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


class KeyLen(base_tests.SimpleDataPlane):

    def InsertTable(self,field_id,offset,len,table_id,table_type,match_field_num,table_name,key_len):

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
        msg.key_len = key_len
        for m in msg.match:
            msg.key_len += m.len
        self.controller.message_send(msg)

    def InsertFlow(self,field_id,offset,len,value,mask,table_id,ins):

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

        self.controller.message_send(request)

    def SetValueMask(self,valuestr,maskstr):

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

    def runTest(self):
        sleep(1)
        logging.info("Running goto_table Test")
        of_ports = config["port_map"].keys()
        of_ports.sort()

        num=300
        step = num//2
'''
        while(True){
            self.InsertTable(0x0000,96,16,0,0,1,"first flow table",num)


            (response, raw) = self.controller.poll(ofp.POFT_ERROR,timeout=5)
            if(response is not None){
                num = num - step
                }
            else{
                self.DeleteTable(0x0000,96,16,0,0,1,"first flow table",num)
                num = num + step
                }
            step = step//2
        }
'''
