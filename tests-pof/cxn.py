"""
Connection test cases

"""

import time
import sys
import logging

import unittest
import random

from oftest import config
import oftest.controller as controller
import ofp
import oftest.dataplane as dataplane

from oftest.testutils import *

class BaseHandshake(unittest.TestCase):
    """
    Base handshake case to set up controller, but do not send hello.
    """

    def controllerSetup(self):
        # clean_shutdown should be set to False to force quit app
        #self.clean_shutdown = True
        # disable initial hello so hello is under control of test
        self.controller.initial_hello = False

        #self.controller.start()
        #self.controllers.append(con)

    def setUp(self):
        logging.info("** START TEST CASE " + str(self))

        self.controller = controller.Controller(host=config["controller_host"],
                                                port=config["controller_port"])
        self.default_timeout = test_param_get('default_timeout',
                                              default=2)
        self.controller.start()
    def tearDown(self):
        logging.info("** END TEST CASE " + str(self))
        #for con in self.controllers:
        self.controller.shutdown()
        #if self.clean_shutdown:
        self.controller.join()

    def runTest(self):
        # do nothing in the base case
        pass

    def assertTrue(self, cond, msg):
        if not cond:
            logging.error("** FAILED ASSERTION: " + msg)
        unittest.TestCase.assertTrue(self, cond, msg)

class HandshakeNoHello(BaseHandshake):
    """
    TCP connect to switch, but do not sent hello,
    and wait for disconnect.
    """
    def runTest(self):
        self.controllerSetup()
        self.controller.connect(self.default_timeout)

        logging.info("TCP Connected " + 
                     str(self.controller.switch_addr))
        logging.info("Hello not sent, waiting for timeout")

        # wait for controller to die
        self.assertTrue(self.controller.wait_disconnected(timeout=10),
                        "Not notified of controller disconnect")

class HandshakeNoFeaturesRequest(BaseHandshake):
    """
    TCP connect to switch, send hello, but do not send features request,
    and wait for disconnect.
    """
    def runTest(self):
        self.controllerSetup()
        self.controller.connect(self.default_timeout)

        logging.info("TCP Connected " + 
                     str(self.controller.switch_addr))
        logging.info("Sending hello")
        self.controller.message_send(ofp.message.hello())

        logging.info("Features request not sent, waiting for timeout")

        # wait for controller to die
        self.assertTrue(self.controller.wait_disconnected(timeout=10),
                        "Not notified of controller disconnect")

class HandshakeNoSetConfig(BaseHandshake):
    """
    TCP connect to switch, send hello and features request, but do not send set config,
    and wait for disconnect.
    """
    def runTest(self):
        self.controllerSetup()
        self.controller.connect(self.default_timeout)

        logging.info("TCP Connected " + 
                     str(self.controller.switch_addr))
        logging.info("Sending hello")
        self.controller.message_send(ofp.message.hello())

        logging.info("Send features request, waiting for features reply")
        request = ofp.message.features_request()
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get features reply")
        self.assertEqual(response.type, ofp.POFT_FEATURES_REPLY,
                         'response is not features reply')
        self.assertEqual(request.xid, response.xid,
                         'response xid != request xid')
 
        logging.info("Set config not sent, waiting for timeout")
        # wait for controller to die
        self.assertTrue(self.controller.wait_disconnected(timeout=10),
                        "Not notified of controller disconnect")


class HandshakeNoGetConfigRequest(BaseHandshake):
    """
    TCP connect to switch, send hello, features request, and set config, but do not send get config request request,
    and wait for disconnect.
    """
    def runTest(self):
        self.controllerSetup()
        self.controller.connect(self.default_timeout)

        logging.info("TCP Connected " + 
                     str(self.controller.switch_addr))
        logging.info("Sending hello")
        self.controller.message_send(ofp.message.hello())

        logging.info("Send features request, waiting for features reply")
        request = ofp.message.features_request()
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get features reply")
        self.assertEqual(response.type, ofp.POFT_FEATURES_REPLY,
                         'response is not features reply')
        self.assertEqual(request.xid, response.xid,
                         'response xid != request xid')

        logging.info("Send set config")
        request = ofp.message.set_config()
        temp = self.controller.message_send(request)

        logging.info("Get config request not sent, waiting for timeout")

        # wait for controller to die
        self.assertTrue(self.controller.wait_disconnected(timeout=10),
                        "Not notified of controller disconnect")

class CompleteHandshakeAndKeepAlive(BaseHandshake):
    """
    Set up controller and complete handshake, keep alive.
    """
    def runTest(self):
        self.controllerSetup()
        self.controller.connect(self.default_timeout)

        logging.info("TCP Connected " + 
                     str(self.controller.switch_addr))
        logging.info("Sending hello")
        self.controller.message_send(ofp.message.hello())

        logging.info("Send features request, waiting for features reply")
        request = ofp.message.features_request()
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get features reply")
        self.assertEqual(response.type, ofp.POFT_FEATURES_REPLY,
                         'response is not features reply')
        self.assertEqual(request.xid, response.xid,
                         'response xid != request xid')

        logging.info("Send set config")
        request = ofp.message.set_config()
        temp = self.controller.message_send(request)

        logging.info("Send get config request, waiting for get config reply")
        request = ofp.message.get_config_request()
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get get config reply")
        self.assertEqual(response.type, ofp.POFT_GET_CONFIG_REPLY,
                         'response is not get config reply')
        self.assertEqual(request.xid, response.xid,
                         'response xid != request xid')

        logging.info("Send echo request, to verify the liveness of a controller-switch connection")
        request = ofp.message.echo_request()
        response, pkt = self.controller.transact(request)
        self.assertTrue(response is not None,
                        "Did not get get echo reply")
        self.assertEqual(response.type, ofp.POFT_ECHO_REPLY,
                         'response is not echo reply')
        self.assertEqual(request.xid, response.xid,
                         'response xid != request xid')
