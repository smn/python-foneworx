import os, sys

from twisted.trial.unittest import TestCase
from twisted.internet.defer import inlineCallbacks
from twisted.internet.protocol import ClientCreator
from twisted.internet import reactor
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.python import log

from houston.client import Client, Connection
from houston.utils import dict_to_xml, api_response_to_dict
from houston.errors import ApiException
from houston import protocol

class HoustonProtocol(protocol.HoustonProtocol):
    pass
    
class TwistedConnection(Connection):
    
    def __init__(self, hostname, port):
        self.hostname = hostname
        self.port = port
        self.creator = ClientCreator(reactor, HoustonProtocol)
    
    @inlineCallbacks
    def send(self, dictionary):
        # reroute the remote calls to local calls for testing
        api_request = dict_to_xml(dictionary)
        log.msg("Sending XML: %s" % api_request)
        
        protocol = yield self.creator.connectTCP(self.hostname, self.port)
        api_response = yield protocol.send_xml(api_request)
        response = api_response_to_dict(api_response)
        log.msg("Received Dict: %s" % response)
        if response.get('error_type'):
            raise ApiException(response['error_type'], api_response)
        log.msg('Returning: %s' % response)
        returnValue(response)
    


class HoustonConnectionTestCase(TestCase):
    
    def setUp(self):
        self.username = os.environ['USERNAME']
        self.password = os.environ['PASSWORD']
        self.client = Client(self.username, self.password, 
                                connection=TwistedConnection(
                                    'www.fwxgwsa.co.za',
                                    50000,
                                ))
        # log.startLogging(sys.stdout)
    
    def tearDown(self):
        pass
    
    @inlineCallbacks
    def test_login(self):
        session_id = yield self.client.login()
        log.msg("Got session id: %s" % session_id)
    
    @inlineCallbacks
    def test_logout(self):
        status = yield self.client.logout()
        log.msg("Status: %s" % status)
    
    @inlineCallbacks
    def test_new_messages(self):
        new_messages = yield self.client.new_messages()
        log.msg("New messages: %s" % new_messages)