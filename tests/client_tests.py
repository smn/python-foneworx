# coding=utf-8
from foneworx.client import Client, Status
from foneworx.errors import ApiException
from twisted.trial.unittest import TestCase
from twisted.python import log
from twisted.internet.defer import inlineCallbacks, returnValue
from datetime import datetime, timedelta
from tests.utils import *

class FoneworxClientTestCase(TestCase):
    
    def setUp(self):
        self.client = Client('username', 'password', 
                                connection=TestConnection())
    
    def tearDown(self):
        pass
    
    def test_dict_to_xml(self):
        """dict to xml should recursively be able to parse dicts
        and output neat XML!"""
        d = {
            "hello": [{
                "world": [{
                    "recursive": [{
                        "i": "am"
                    }]
                }]
            }]
        }
        xml = dict_to_xml(d, root=Element("testing"))
        xml_string = tostring(xml, 'utf-8')
        xml_test = u"<testing><hello><world><recursive><i>am" \
                    "</i></recursive></world></hello></testing>"
        self.assertEquals(xml_string, xml_test)
    
    def test_xml_to_dict(self):
        """xml to dict should do the opposite of dict_to_xml"""
        xml = fromstring(u"<testing><hello><world><recursive><i>am" \
                    "</i></recursive></world></hello></testing>")
        testing, dictionary = xml_to_dict(xml)
        self.assertEquals(testing, "testing")
        self.assertEquals(dictionary, {
            "hello": [{
                "world": [{
                    "recursive": [{
                        "i": "am"
                    }]
                }]
            }]
        })
    
    def test_dict_to_xml_unicode(self):
        """shouldn't trip on unicode characters"""
        d = {
            "hello": u"wørl∂"
        }
        xml = dict_to_xml(d, root=Element("unicode"))
        xml_string = tostring(xml, 'utf-8')
    
        
    @inlineCallbacks
    def test_login(self):
        session_id = yield self.client.login()
        self.assertEquals(session_id, 'my_session_id')
    
    @inlineCallbacks
    def test_session_id_property(self):
        session_id = yield self.client.get_session_id()
        self.assertEquals(session_id, 'my_session_id')
    
    @inlineCallbacks
    def test_logout(self):
        status = yield self.client.logout()
        self.assertEquals(status, 'Success')
    
    @inlineCallbacks
    def test_new_messages(self):
        response = yield self.client.new_messages()
        self.assertEquals(response, [{
            'parent_sms_id': 'parent sms id 1', 
            'msisdn': '+27123456789', 
            'destination': '+27123456789', 
            'timereceived': datetime(2010, 7, 14, 12, 15, 11), 
            'message': 'hello world', 
            'sms_id': 'sms id 1'
        },
        {   
            'parent_sms_id': 'parent sms id 2',
            'msisdn': '+27123456789',
            'destination': '+27123456789',
            'timereceived': datetime(2010, 7, 14, 12, 15, 11),
            'message': 'hello world',
            'sms_id': 'sms id 2'
        }])
    
    @inlineCallbacks
    def test_new_messages_since_timestamp(self):
        response = yield self.client.new_messages(since=datetime.now())
        self.assertEquals(response, [{
            'parent_sms_id': 'parent sms id 1', 
            'msisdn': '+27123456789', 
            'destination': '+27123456789', 
            'timereceived': datetime(2010, 7, 14, 12, 15, 11), 
            'message': 'hello world', 
            'sms_id': 'sms id 1'
        }])
    
    @inlineCallbacks
    def test_delete_messages(self):
        response = yield self.client.delete_message('sms id 1')
        self.assertEquals(response, "Success")
    
    @inlineCallbacks
    def test_send_messages(self):
        response = yield self.client.send_messages([{
            "msisdn": "+27123456789",
            "message": "hello world",
            "rule": "?",
            "send_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }, {
            "msisdn": "+27123456789",
            "message": "hello world",
            "rule": "?",
            "send_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }])
        # check the mocked responses from the API
        self.assertEquals([d['submit'] for d in response], ['fail', 'success'])
        self.assertEquals([d['sms_id'] for d in response], ['sms 1', 'sms 2'])
    
    @inlineCallbacks
    def test_sent_messages(self):
        response = yield self.client.sent_messages()
        self.assertTrue(response)
        self.assertEquals(len(response), 1)
        # get the dict
        sms = response.pop()
        self.assertEquals(sms, {
            'sms_id': 'sms id 1',
            'status_id': Status('3'),
            'status_text': 'Delivered',
            'time_submitted': datetime(2010, 7, 20, 11, 00,00),
            'time_processed': datetime(2010, 7, 20, 12, 00,00),
            'rule': None,
            'short_message': 'Hello World',
            'destination_addr': '+27123456789'
        })
    
    @inlineCallbacks
    def test_delete_sent_message(self):
        response = yield self.client.delete_sent_message('sms id 1')
        self.assertEquals(response, "Success")
        response = yield self.client.delete_sent_message('sms id 2')
        self.assertEquals(response, 'fail')
        self.assertFailure(
            self.client.delete_sent_message('an obviously wrong id'), # a deferred
            ApiException
        )
