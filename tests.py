# coding=utf-8
from xml.etree.ElementTree import Element, tostring, fromstring
from houston.client import Client, Connection, Status
from houston.utils import xml_to_dict, dict_to_xml, Dispatcher
from houston.errors import ApiException
from unittest import TestCase
from twisted.python import log
from twisted.internet.defer import inlineCallbacks, returnValue
from datetime import datetime, timedelta

class TestDispatcher(Dispatcher):
    """
    This dispatcher mimicks the responses we get back from the 
    Foneworx XML api (according to their API docs). Instead of going
    over the network I send back the XML response straight away.
    """
    
    def do_login(self, xml):
        return """<?xml version="1.0"?>
        <sms_api>
            <error_type></error_type>
            <session_id>my_session_id</session_id>
            <api_doc_version></api_doc_version>
        </sms_api>
        """
    
    def do_logout(self, xml):
        return """<?xml version="1.0"?>
        <sms_api>
            <status>ok</status>
            <error_type></error_type>
        </sms_api>
        """
    
    def do_newmessages(self, xml):
        # if the sms time parameter is given then
        # only return a subset
        if xml.findall('action_content/smstime'):
            return """<?xml version="1.0"?>
            <sms_api>
                <error_type></error_type>
                <sms>
                    <sms_id>sms id 1</sms_id>
                    <msisdn>+27123456789</msisdn>
                    <message>hello world</message>
                    <destination>+27123456789</destination>
                    <timereceived>20100714121511</timereceived>
                    <parent_sms_id>parent sms id 1</parent_sms_id>
                </sms>
            </sms_api>
            """
        else:
            return """<?xml version="1.0"?>
            <sms_api>
                <error_type></error_type>
                <sms>
                    <sms_id>sms id 1</sms_id>
                    <msisdn>+27123456789</msisdn>
                    <message>hello world</message>
                    <destination>+27123456789</destination>
                    <timereceived>20100714121511</timereceived>
                    <parent_sms_id>parent sms id 1</parent_sms_id>
                </sms>
                <sms>
                    <sms_id>sms id 2</sms_id>
                    <msisdn>+27123456789</msisdn>
                    <message>hello world</message>
                    <destination>+27123456789</destination>
                    <timereceived>20100714121511</timereceived>
                    <parent_sms_id>parent sms id 2</parent_sms_id>
                </sms>
            </sms_api>
            """

    def do_deletenewmessages(self, xml):
        return """<?xml version="1.0"?>
        <sms_api>
            <error_type></error_type>
            <status>ok</status>
        </sms_api>
        """
    
    def do_sendmessages(self, xml):
        return """<?xml version="1.0"?>
        <sms_api>
            <sms>
                <msisdn></msisdn>
                <message></message>
                <source_addr></source_addr>
                <sentby></sentby>
                <smstype></smstype>
                <submit>fail</submit>
                <sms_id>sms 1</sms_id>
            </sms>
            <sms>
                <msisdn></msisdn>
                <message></message>
                <source_addr></source_addr>
                <sentby></sentby>
                <smstype></smstype>
                <submit>success</submit>
                <sms_id>sms 2</sms_id>
            </sms>
        </sms_api>
        """
    
    def do_sentmessages(self, xml):
        return """<?xml version="1.0"?>
        <sms_api>
            <error_type></error_type>
            <sms>
                <sms_id>sms id 1</sms_id>
                <status_id>3</status_id>
                <status_text>Delivered</status_text>
                <time_submitted>20100720110000</time_submitted>
                <time_processed>20100720120000</time_processed>
                <rule></rule>
                <short_message>Hello World</short_message>
                <destination_addr>+27123456789</destination_addr>
            </sms>
        </sms_api>
        """
    
    def do_deletesentmessages(self, xml):
        sms_id_node = xml.find('action_content/sms_id')
        if sms_id_node.text == 'sms id 1':
            return """<?xml version="1.0"?>
            <sms_api>
                <error_type></error_type>
                <status>ok</status>
            </sms_api>
            """
        elif sms_id_node.text == 'sms id 2':
            return """<?xml version="1.0"?>
            <sms_api>
                <error_type></error_type>
                <status>fail</status>
            </sms_api>
            """
        else:
            return """<?xml version="1.0"?>
            <sms_api>
                <error_type>la merde a frappé le ventilateur</error_type>
                <status></status>
            </sms_api>
            """

class TestConnection(Connection):
    
    def __init__(self):
        self.dispatcher = TestDispatcher()
    
    @inlineCallbacks
    def send(self, dictionary):
        # reroute the remote calls to local calls for testing
        api_action = dictionary['api_action']
        sent_xml = dict_to_xml(dictionary, Element("sms_api"))
        print "Sending XML: %s" % tostring(sent_xml)
        received_xml = yield self.dispatcher.dispatch(api_action, sent_xml)
        xml = fromstring(received_xml)
        print "Received XML: %s" % tostring(xml)
        sms_api, response = xml_to_dict(xml)
        print "Received Dict: %s" % response
        # if at any point, we get this error something went wrong
        if response.get('error_type'):
            raise ApiException(response['error_type'], tostring(xml))
        print 'Returning', response
        returnValue(response)
    

class HoustonTestCase(TestCase):
    
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
            "hello": "wørl∂"
        }
        xml = dict_to_xml(d, root=Element("unicode"))
        xml_string = tostring(xml, 'utf-8')
    
        
    @inlineCallbacks
    def test_login(self):
        session_id = yield self.client.login()
        self.assertEquals(session_id, 'my_session_id')
    
    @inlineCallbacks
    def test_session_id_property(self):
        session_id = yield self.client.session_id
        self.assertEquals(session_id, 'my_session_id')
    
    @inlineCallbacks
    def test_logout(self):
        status = yield self.client.logout()
        self.assertEquals(status, 'ok')
    
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
    
    def test_new_messages_since_timestamp(self):
        response = self.client.new_messages(since=datetime.now())
        self.assertEquals(response, [{
            'parent_sms_id': 'parent sms id 1', 
            'msisdn': '+27123456789', 
            'destination': '+27123456789', 
            'timereceived': datetime(2010, 7, 14, 12, 15, 11), 
            'message': 'hello world', 
            'sms_id': 'sms id 1'
        }])
    
    def test_delete_messages(self):
        response = self.client.delete_message('sms id 1')
        self.assertEquals(response, "ok")
    
    def test_send_messages(self):
        response = self.client.send_messages([{
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
    
    def test_sent_messages(self):
        response = self.client.sent_messages()
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
    
    def test_deletesentmessages(self):
        response = self.client.delete_sentmessages('sms id 1')
        self.assertEquals(response, "ok")
        response = self.client.delete_sentmessages('sms id 2')
        self.assertEquals(response, 'fail')
        self.assertRaises(ApiException, self.client.delete_sentmessages, 
                            'an obviously wrong id')
