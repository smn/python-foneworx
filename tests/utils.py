# coding=utf-8
from xml.etree.ElementTree import Element, tostring, fromstring
from twisted.internet.defer import inlineCallbacks, returnValue
from twisted.python import log
from houston.utils import xml_to_dict, dict_to_xml, Dispatcher
from houston.client import Connection
from houston.errors import ApiException

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
            <status>Success</status>
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
            <change>Success</change>
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
                <change>Success</change>
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
        log.msg("Sending XML: %s" % tostring(sent_xml))
        received_xml = yield self.dispatcher.dispatch(api_action, sent_xml)
        xml = fromstring(received_xml)
        log.msg("Received XML: %s" % tostring(xml))
        sms_api, response = xml_to_dict(xml)
        log.msg("Received Dict: %s" % response)
        # if at any point, we get this error something went wrong
        if response.get('error_type'):
            raise ApiException(response['error_type'], tostring(xml))
        log.msg('Returning: %s' % response)
        returnValue(response)
    

