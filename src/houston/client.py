from houston.utils import dict_to_xml, xml_to_dict
from xml.etree.ElementTree import Element, tostring, fromstring
import logging
logging.basicConfig(level=logging.DEBUG)

class Connection(object): 
    
    def send(self, dictionary):
        logging.debug("Sending dict: %s" % dictionary)
        xml = dict_to_xml(dictionary, Element("sms_api"))
        xml_string = tostring(xml, encoding='utf-8')
        logging.debug("Sending XML: %s" % xml_string)
        sms_api, result = xml_to_dict(fromstring(xml_string))
        return result
    
    def __getattr__(self, attname):
        """
        All calls to the connection will automatically be sent
        over the wire to FoneWorx as an API call.
        """
        def sms_api_wrapper(*args, **options):
            options.update({'api_action': attname})
            return self.send(options)
        return sms_api_wrapper

class Client(object):
    
    def __init__(self, username, password, connection_class=Connection):
        self.username = username
        self.password = password
        self.connection = connection_class()
    
    def login(self):
        """Return a session id from the Foneworx API. Session ids time out
        after 10 minutes of inactivity."""
        return self.connection.login(api_username=self.username, 
                                        api_password=self.password)['session_id']
