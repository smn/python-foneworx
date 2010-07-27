from zope.interface import implements
from twisted.python import usage, log
from twisted.python.log import logging
from twisted.application.service import IServiceMaker
from twisted.application import internet
from twisted.plugin import IPlugin
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineOnlyReceiver, LineReceiver
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue
from houston.client import Client, Connection
from houston.errors import HoustonException, ApiException
from xml.etree.ElementTree import Element, tostring, fromstring
from houston.utils import xml_to_dict, dict_to_xml
from cStringIO import StringIO

class Options(usage.Options):
    optParameters = [
        ['host', 'h', 'www.fwxgwsa.co.za', 'Foneworx API host', str],
        ['port', 'p', 50000, 'Foneworx API port', int],
        ['username', 'u', 'xxxx', 'Foneworx username', str],
        ['password', 'p', 'yyyy', 'Foneworx password', str]
    ]
    
    optFlags = [
        ['debug', 'd', 'Turn on debug output'],
    ]

class ConnectionWrapper(Connection):
    
    def __init__(self, protocol):
        self.protocol = protocol
    
    @inlineCallbacks
    def send(self, *args, **kwargs):
        response = yield self.protocol.send(*args, **kwargs)
        returnValue(response)
    

class HoustonProtocol(LineReceiver):
    
    delimiter = chr(0)
    
    def __init__(self, username, password, debug):
        self.username = username
        self.password = password
        self.debug = debug
        self.onXMLReceived = None
        self.setRawMode()
        self.buffer = ''
    
    def rawDataReceived(self, data):
        log.msg("Received raw data: %s" % data, logLevel=logging.DEBUG)
        self.buffer += data
    
    def xml_received(self, data):
        log.msg("Received xml: %s" % data, logLevel=logging.DEBUG)
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
            raise RuntimeError, "onXMLReceived already initialized before sending"
        self.onXMLReceived = Deferred()
        if self.debug:
            log.msg("Sending line: %s" % line, logLevel=logging.DEBUG)
        LineReceiver.sendLine(self, line)
        return self.onXMLReceived
    
    def connectionLost(self, reason):
        log.err("Connection lost, reason: %s" % reason)
        if self.buffer:
            log.msg('calling xml_received with %s' % self.buffer, logLevel=logging.DEBUG)
            self.xml_received(self.buffer)
    
    def connectionMade(self):
        log.msg("Connection made")
        self.client = Client(self.username, self.password, 
                                connection=ConnectionWrapper(self))
        log.msg("Logging in...")
        self.client.login()
    
    @inlineCallbacks
    def send(self, dictionary):
        # reroute the remote calls to local calls for testing
        api_action = dictionary['api_action']
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
        

class HoustonFactory(ClientFactory):
    
    def __init__(self, **options):
        self.options = options
    
    def startedConnecting(self, connector):
        log.msg("Started connecting")
    
    def clientConnectionFailed(self, connector, reason):
        log.err("Client connection failed")
        log.err(reason)
    
    def clientConnectionLost(self, connector, reason):
        log.err("Client connection lost")
        log.err(reason)
        
    def startFactory(self):
        log.msg('Starting factory')
    
    def stopFactory(self):
        log.msg('Stopping factory')
    
    def buildProtocol(self, addr):
        log.msg('Building protocol')
        return HoustonProtocol(**self.options)
    

class ServiceMaker(object):
    implements(IServiceMaker, IPlugin)
    tapname = "houston"
    description = "Run houston through some basic tests"
    options = Options
    
    def makeService(self, options):
        host, port = options.pop('host'), options.pop('port')
        return internet.TCPClient(host, port, HoustonFactory(**options))

serviceMaker = ServiceMaker()
