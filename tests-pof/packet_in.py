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


class PacketIn(base_tests.SimpleProtocol):
    num = 0
    def pktin_handler(self, controller, msg, msg_raw):
        self.num += 1
        return True

    def runTest(self):
        self.controller.register(ofp.POFT_PACKET_IN, self.pktin_handler)

        while True:
            time.sleep(1)
            print self.num
