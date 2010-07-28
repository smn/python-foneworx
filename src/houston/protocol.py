from twisted.python import log
from twisted.python.log import logging
from twisted.protocols.basic import LineReceiver
from twisted.internet import error
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue
from houston.errors import HoustonException
from houston.utils import *

class HoustonProtocol(LineReceiver):
    
    delimiter = chr(0)
    
    def __init__(self):
        self.onXMLReceived = None
        self.setRawMode()
        self.buffer = ''
    
    def rawDataReceived(self, data):
        log.msg("Received raw data: %s" % data, logLevel=logging.DEBUG)
        self.buffer += data
    
    def xml_received(self, data):
        if not self.onXMLReceived:
            raise HoustonException, "onXMLReceived not initialized for receiving"
        self.onXMLReceived.callback(data)
        self.onXMLReceived = None # reset
        self.buffer = '' # reset
    
    def lineLengthExceeded(self, line):
        log.err("Line length exceeded!")
        log.err(line)
    
    def send_xml(self, xml):
        return self.sendLine("""<?xml version="1.0" encoding="utf-8"?>%s""" \
                                % tostring(xml))
    
    def sendLine(self, line):
        if self.onXMLReceived:
            raise HoustonException, "onXMLReceived already initialized before sending"
        self.onXMLReceived = Deferred()
        log.msg("Sending line: %s" % line, logLevel=logging.DEBUG)
        LineReceiver.sendLine(self, line)
        return self.onXMLReceived
    
    def connectionLost(self, reason):
        if reason.check(error.ConnectionDone):
            log.msg("Connection closed, processing received data")
        else:
            log.err("Connection lost, reason: %s" % reason)
        if self.buffer:
            log.msg('calling xml_received with %s' % self.buffer, logLevel=logging.DEBUG)
            self.xml_received(self.buffer)
    
    def connectionMade(self):
        log.msg("Connection made")
    
    @inlineCallbacks
    def send(self, dictionary):
        # reroute the remote calls to local calls for testing
        sent_xml = dict_to_xml(dictionary, Element("sms_api"))
        log.msg("Sending XML: %s" % tostring(sent_xml), logLevel=logging.DEBUG)
        received_xml = yield self.send_xml(sent_xml)
        xml = fromstring(received_xml)
        log.msg("Received XML: %s" % tostring(xml), logLevel=logging.DEBUG)
        sms_api, response = xml_to_dict(xml)
        log.msg("Received Dict: %s" % response, logLevel=logging.DEBUG)
        # if at any point, we get this error something went wrong
        if response.get('error_type'):
            raise ApiException(response['error_type'], tostring(xml))
        returnValue(response)
        
