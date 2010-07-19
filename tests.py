# coding=utf-8
from xml.etree.ElementTree import Element, tostring, fromstring
from houston.client import Client, Connection
from houston.utils import xml_to_dict, dict_to_xml, Dispatcher
from houston.errors import ApiException
from unittest import TestCase
import logging
from datetime import datetime, timedelta

class TestDispatcher(Dispatcher):
    
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

class TestConnection(Connection):
    
    def __init__(self):
        self.dispatcher = TestDispatcher()
    
    def send(self, dictionary):
        # reroute the remote calls to local calls for testing
        api_action = dictionary['api_action']
        sent_xml = dict_to_xml(dictionary, Element("sms_api"))
        logging.debug("Sending XML: %s" % tostring(sent_xml))
        xml = fromstring(self.dispatcher.dispatch(api_action, sent_xml))
        logging.debug("Received XML: %s" % tostring(xml))
        sms_api, response = xml_to_dict(xml)
        logging.debug("Received Dict: %s" % response)
        # if at any point, we get this error something went wrong
        if response.get('error_type'):
            raise ApiException(response['error_type'], tostring(xml))
        return response
    

class HoustonTestCase(TestCase):
    
    def setUp(self):
        self.client = Client('username', 'password', 
                                connection_class=TestConnection)
    
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
    
    def test_login(self):
        session_id = self.client.login()
        self.assertEquals(session_id, 'my_session_id')
        
    def test_session_id_property(self):
        session_id = self.client.session_id
        self.assertEquals(session_id, 'my_session_id')
    
    def test_logout(self):
        status = self.client.logout()
        self.assertEquals(status, 'ok')
    
    def test_new_messages(self):
        response = self.client.new_messages()
        self.assertEquals(response, [{
            'parent_sms_id': 'parent sms id 1', 
            'msisdn': '+27123456789', 
            'destination': '+27123456789', 
            'timereceived': '20100714121511', 
            'message': 'hello world', 
            'sms_id': 'sms id 1'
        },
        {   
            'parent_sms_id': 'parent sms id 2',
            'msisdn': '+27123456789',
            'destination': '+27123456789',
            'timereceived': '20100714121511',
            'message': 'hello world',
            'sms_id': 'sms id 2'
        }])

    def test_new_messages_since_timestamp(self):
        response = self.client.new_messages(since=datetime.now())
        self.assertEquals(response, [{
            'parent_sms_id': 'parent sms id 1', 
            'msisdn': '+27123456789', 
            'destination': '+27123456789', 
            'timereceived': '20100714121511', 
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
