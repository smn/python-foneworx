from zope.interface import implements

from twisted.python import usage, log
from twisted.python.log import logging
from twisted.application.service import IServiceMaker
from twisted.application import internet
from twisted.plugin import IPlugin
from twisted.internet.protocol import ClientFactory, ConnectionWrapper
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue
from twisted.internet import error

from houston.client import Client, Connection
from houston import protocol

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

class HoustonProtocol(protocol.HoustonProtocol):
    
    def connectionMade(self):
        log.msg("Connection made")
        self.client = Client(self.username, self.password, 
                                connection=ConnectionWrapper(self))
        log.msg("Logging in...")
        self.client.login()
    
    

class HoustonFactory(ClientFactory):
    
    def __init__(self, **options):
        self.options = options
    
    def startedConnecting(self, connector):
        log.msg("Started connecting")
    
    def clientConnectionFailed(self, connector, reason):
        log.err("Client connection failed")
        log.err(reason)
    
    def clientConnectionLost(self, connector, reason):
        if not reason.check(error.ConnectionDone):
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
