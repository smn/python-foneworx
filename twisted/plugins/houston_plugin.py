from zope.interface import implements
from twisted.python import usage, log
from twisted.application.service import IServiceMaker
from twisted.application import internet
from twisted.plugin import IPlugin
from twisted.internet.protocol import ClientFactory
from twisted.protocols.basic import LineOnlyReceiver
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue
from houston.client import Client, Connection
from xml.etree.ElementTree import Element, tostring, fromstring
from houston.utils import xml_to_dict, dict_to_xml

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

class HoustonProtocol(LineOnlyReceiver):
    delimiter = chr(0)
    
    def __init__(self, username, password, debug):
        self.debug = debug
        self.onConnectionMade = Deferred()
        self.onLineReceived = None
        # left off here...
        self.connection = TwistedHoustonConnection()
        self.connection.
    
    def lineReceived(self, line):
        log.msg("Received line: %s" % line)
        if not self.onLineReceived:
            raise RuntimeError, "onLineReceived not initialized for receiving"
        self.onLineReceived.callback(line)
        self.onLineReceived = None # reset
    
    def lineLengthExceeded(self, line):
        log.err("Line length exceeded!")
        log.err(line)
    
    def sendLine(self, line):
        
        if self.onLineReceived:
            raise RuntimeError, "onLineReceived already initialized before sending"
        
        self.onLineReceived = Deferred()
        if self.debug:
            log.msg("Sending line: %s" % line)
        LineOnlyReceiver.sendLine(self, line)
        return self.onLineReceived
    
    def connectionLost(self, reason):
        log.err("Connection lost, reason: %s" % reason)
    
    def connectionMade(self):
        log.msg("Connection made")
        self.onConnectionMade.callback(self)
    

class TwistedHoustonConnection(Connection):
    
    @inlineCallbacks
    def send(self, dictionary):
        # reroute the remote calls to local calls for testing
        api_action = dictionary['api_action']
        sent_xml = dict_to_xml(dictionary, Element("sms_api"))
        logging.debug("Sending XML: %s" % tostring(sent_xml))
        received_xml = yield self.sendLine(sent_xml)
        xml = fromstring(received_xml)
        logging.debug("Received XML: %s" % tostring(xml))
        sms_api, response = xml_to_dict(xml)
        logging.debug("Received Dict: %s" % response)
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
