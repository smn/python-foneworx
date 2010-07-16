from houston.utils import dict_to_xml, xml_to_dict
from xml.etree.ElementTree import Element, tostring, fromstring
from datetime import datetime, timedelta
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
        self._session_id = None
    
    @property
    def session_id(self):
        """Session ids time out after 10 minutes of inactivity."""
        if not self._session_id:
            self._session_id = self.login()
        return self._session_id
    
    def login(self):
        """Return a session id from the Foneworx API. """
        response = self.connection.login(api_username=self.username, 
                                            api_password=self.password)
        return response.get('session_id')
    
    def logout(self):
        response = self.connection.logout(api_session_id=self.session_id)
        return response.get('status')
    
    def new_messages(self):
        response = self.connection.newmessages(actioncontent={})
        return response.get('sms')