import os, sys, time
from datetime import datetime
from getpass import getpass

from twisted.trial.unittest import TestCase
from twisted.internet.defer import inlineCallbacks
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.python import log

from foneworx.client import Client, TwistedConnection
from foneworx.utils import dict_to_xml, api_response_to_dict, tostring, Element
from foneworx.errors import ApiException
from foneworx import protocol

class FoneworxConnectionTestCase(TestCase):
    """Not to be automated, use for manual testing only"""
    
    def setUp(self):
        self.username = os.environ.get('USERNAME') or raw_input("Username: ")
        self.password = os.environ.get('PASSWORD') or getpass("Pasword: ")
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
        self.assertEquals(status, 'Success')
        log.msg("Status: %s" % status)
    
    @inlineCallbacks
    def test_new_messages(self):
        new_messages = yield self.client.new_messages(since=datetime(2010,7,26))
        self.assertTrue(isinstance(new_messages, list))
        log.msg("New messages: %s" % new_messages)
    
    @inlineCallbacks
    def test_send_messages(self):
        sent_messages = yield self.client.send_messages([
            {
                'msisdn': os.environ.get('MSISDN') or raw_input('enter msisdn: '),
                'message': 'hello world from test send messages'
            }
        ])
        self.assertTrue(isinstance(sent_messages, list))
        self.assertTrue(len(sent_messages), 1)
        sent_sms = sent_messages.pop()
        self.assertEquals(sent_sms['submit'], 'Success')
    
    @inlineCallbacks
    def test_sent_messages(self):
        sent_messages = yield self.client.sent_messages(
            give_detail=1, 
            since=datetime(2000,1,1)
        )
        self.assertTrue(isinstance(sent_messages, list))
        self.assertTrue(len(sent_messages))
    
    @inlineCallbacks
    def test_full_stack(self):
        start = datetime.now()
        print """Please send a test SMS to Foneworx in order to fill""" \
                """ the inbox."""
        
        while True:
            print 'Checking for new SMSs every 2 seconds'
            received = yield self.client.new_messages(since=start)
            if received:
                break
            time.sleep(2)
        sms = received.pop()
        print 'Replying to an SMS received from', sms['msisdn']
        sent = yield self.client.send_messages([{
            'msisdn': sms['msisdn'],
            'message': "Hi! you said: %s" % sms['message']
        }])
        print 'Waiting until delivered'
        while True:
            statuses = yield self.client.sent_messages(since=start, give_detail=True)
            if statuses:
                matching_statuses = [status for status in statuses 
                                        if (status['destination_addr'] in sms['msisdn'])]
                if matching_statuses:
                    status = matching_statuses.pop()
                    if status['status_text'] == 'Delivered':
                        print 'Delivered!'
                        break
                    else:
                        print 'Not delivered yet:', status['status_text']
                else:
                    print 'Did not find any matching statuses'
            time.sleep(2)
        print 'Deleting the received message'
        delete = yield self.client.delete_message(sms['sms_id'])
        print 'Deleted:', delete
        print 'Deleting the sent message'
        delete = yield self.client.delete_sent_message(status['sms_id'])
        print 'Deleted:', delete
        print 'Logging out'
        logout = yield self.client.logout()
        print 'Logged out:', logout