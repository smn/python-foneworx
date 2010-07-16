# coding=utf-8
from xml.etree.ElementTree import Element, tostring, fromstring
from houston.client import Client, Connection
from houston.utils import xml_to_dict, dict_to_xml, Dispatcher
from houston.errors import ApiException
from unittest import TestCase
import logging

class TestConnection(Dispatcher):
    
    def send(self, dictionary):
        # reroute the remote calls to local calls for testing
        api_action = dictionary['api_action']
        sent_xml = dict_to_xml(dictionary, Element("sms_api"))
        xml = fromstring(self.dispatch(api_action, sent_xml))
        sms_api, response = xml_to_dict(xml)
        # if at any point, we get this error something went wrong
        if response.get('error_type'):
            raise ApiException(response['error_type'], tostring(xml))
        return response
    
    def __getattr__(self, attname):
        """
        All calls to the connection will automatically be sent
        over the wire to FoneWorx as an API call.
        """
        def sms_api_wrapper(**options):
            options.update({'api_action': attname})
            return self.send(options)
        return sms_api_wrapper
    
    def do_login(self, xml):
        return """<?xml version="1.0"?>
        <sms_api>
            <error_type></error_type>
            <session_id>my_session_id</session_id>
            <api_doc_version></api_doc_version>
        </sms_api>
        """

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
            "hello": {
                "world": {
                    "recursive": {
                        "i": "am"
                    }
                }
            }
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
            "hello": {
                "world": {
                    "recursive": {
                        "i": "am"
                    }
                }
            }
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