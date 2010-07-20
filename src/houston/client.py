from houston.utils import dict_to_xml, xml_to_dict, Dispatcher
from xml.etree.ElementTree import Element, tostring, fromstring
from datetime import datetime, timedelta
import logging
logging.basicConfig(level=logging.DEBUG)

class Connection(object): 
    
    def send(self, dictionary):
        pass
    
    def __getattr__(self, attname):
        """
        All calls to the connection will automatically be sent
        over the wire to FoneWorx as an API call.
        """
        def sms_api_wrapper(*args, **options):
            options.update({'api_action': attname})
            return self.send(options)
        return sms_api_wrapper

class Status(object):
    
    values = {
        0: "To Be Sent",
        1: "Submitted To Network",
        2: "At Network",
        3: "Delivered",
        4: "Rejected",
        5: "Undelivered",
        6: "Expired",
        9: "Submit Failed",
        10: "Cancelled",
        11: "Scheduled",
        91: "Message Length is Invalid",
        911: "Desitnation Addr Is Invalid",
        988: "Throttling Error",
    }
    
    def __init__(self, status_id):
        self.status_id = int(status_id)
    
    @property
    def id(self):
        return self.status_id
    
    @property
    def text(self):
        return self.values.get(self.id, 'Unknown status')
    
    def __repr__(self):
        return "<Status id: %s, msg: %s>" % (self.id, self.text)


class Convertor(Dispatcher):
    
    def do_datetime(self, string):
        return datetime.strptime(string, '%Y%m%d%H%M%S')
    
    # these do all the same
    do_time_submitted = \
    do_time_processed = \
    do_timereceived = do_datetime
    
    def convert(self, key, value):
        try:
            return key, self.dispatch(key, value)
        except Exception, e:
            return key, value
    

class Client(object):
    
    def __init__(self, username, password, connection_class=Connection):
        self.username = username
        self.password = password
        self.connection = connection_class()
        self._session_id = None
    
    def to_python_values(self, dictionary):
        convertor = Convertor()
        return dict(convertor.convert(*kv) for kv in dictionary.items())
        
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
        response = self.connection.logout(api_sessionid=self.session_id)
        return response.get('status')
    
    def new_messages(self, since=None):
        action_content = {}
        if since:
            action_content.update({
                "smstime": since.strftime("%Y%m%d%H%M%S")
            })
        response = self.connection.newmessages(
            api_sessionid=self.session_id,
            action_content=action_content
        )
        return [self.to_python_values(sms) for sms in response.get('sms')]

    def delete_message(self, sms_id):
        response = self.connection.deletenewmessages(
            api_sessionid=self.session_id,
            action_content={
                'sms_id': sms_id
            }
        )
        return response.get('status')

    def send_messages(self, messages):
        response = self.connection.sendmessages(
            api_sessionid=self.session_id,
            action_content={
                "sms": messages
            }
        )
        return response.get('sms')
    
    def sent_messages(self, **options):
        """
        Available options:
        
        Keyword arguments:
        
        smstime --  if smstime is empty the system will only return new messages 
                    since the last time of this call for this user. if smstime 
                    (format yyyymmddHHMMSS) is filled in, it will return all 
                    message since that time
        
        give_detail --  if you want the message and the destination numbers 
                        returned for each sms (1) - true (0) - false
        
        """
        response = self.connection.sentmessages(
            api_sessionid=self.session_id,
            action_content=options
        )
        return [self.to_python_values(sms) for sms in response.get('sms')]
    
    def delete_sentmessages(self, sms_id):
        response = self.connection.deletesentmessages(
            api_sessionid=self.session_id,
            action_content={
                'sms_id': sms_id
            }
        )
        return response.get('status')
