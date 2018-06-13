import logging

import unittest
import random
import time
import os
import copy
import struct

from oftest import config
import oftest.controller as controller
import ofp
import oftest.dataplane as dataplane
import oftest.parse as parse
import oftest.base_tests as base_tests

from oftest.testutils import *
from time import sleep


class send_packet(base_tests.BaseTest):
    def runTest(self):
        sleep(1)
        #  while True:
        tcp = simple_tcp_packet()
        print(type(tcp))
        binary = bytearray(str(tcp))
        i = struct.unpack_from('!i', binary, 0)
        print(i)
        struct.pack_into('!i', binary, 0, 1)
        i = struct.unpack_from('!i', binary, 0)
        print(i)
        #  self.dataplane.ports[15].send(str(simple_tcp_packet()))
             
