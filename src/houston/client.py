from houston.utils import dict_to_xml, xml_to_dict, Dispatcher
from twisted.internet.defer import Deferred, inlineCallbacks, returnValue
from twisted.python import log
from xml.etree.ElementTree import Element, tostring, fromstring
from datetime import datetime, timedelta

class Connection(object): 
    """Dummy implementation of a connection to the Foneworx SMS XML API"""
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
    """
    Not being used currently
    """
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
        self.status_id = status_id
    
    def __eq__(self, other):
        if isinstance(other, Status):
            return other.id == self.id
        return False
    
    @property
    def id(self):
        return self.status_id
    
    @property
    def text(self):
        return self.values.get(int(self.id), 'Unknown status')
    
    def __repr__(self):
        return "<Status id: %s, msg: %s>" % (self.id, self.text)


class Convertor(Dispatcher):
    """
    Convert a key, value pair to a python object. For now it's primarily
    used for timestamp strings -> datetime objects
    """
    def do_datetime(self, string):
        return datetime.strptime(string, '%Y%m%d%H%M%S')
    
    # these do all the same
    do_time_submitted = \
    do_time_processed = \
    do_timereceived = do_datetime
    
    def do_status_id(self, status_id):
        return Status(status_id)
    
    def convert(self, key, value):
        """
        Wraps the Dispatcher.dispatch to return the original values
        for when a convertor doesn't exist for the given key
        """
        if hasattr(self, "%s%s" % (self.prefix, key.lower())):
            return key, self.dispatch(key, value)
        return key, value
    

class Client(object):
    
    def __init__(self, username, password, connection=Connection()):
        self.username = username
        self.password = password
        self.connection = connection
        self._session_id = None
    
    def to_python_values(self, dictionary):
        """
        Convert a dictionary to more pythonic values
        """
        convertor = Convertor()
        return dict(convertor.convert(*kv) for kv in dictionary.items())
    
    @inlineCallbacks
    def get_new_session_id(self):
        """Get a new session_id from the Foneworx API"""
        session_id = yield self.login()
        returnValue(session_id)
    
    @inlineCallbacks
    def get_session_id(self):
        """
        Session ids time out after 10 minutes of inactivity. Stored locally.
        """
        if not self._session_id:
            self._session_id = yield self.get_new_session_id()
        returnValue(self._session_id)
    
    @inlineCallbacks
    def login(self):
        """
        To log into an account, and get a session var allocated to your login.
        """
        response = yield self.connection.login(api_username=self.username, 
                                            api_password=self.password)
        returnValue(response.get('session_id'))

    @inlineCallbacks
    def logout(self):
        """
        This Function is used to release the sessionid
        """
        session_id = yield self.get_session_id()
        response = yield self.connection.logout(api_sessionid=session_id)
        returnValue(response.get('status'))
    
    @inlineCallbacks
    def new_messages(self, since=None):
        """
        Get New Messages for a user
        
        Arguments:
        
        since --    if since is empty the system will only return new messages 
                    since the last time of this call for this user. if since
                    (datetime object) is filled in, it will return all message 
                    since that time
        
        """
        action_content = {}
        if since:
            action_content.update({
                "smstime": since.strftime("%Y%m%d%H%M%S")
            })
        session_id = yield self.get_session_id()
        response = yield self.connection.newmessages(
            api_sessionid=session_id,
            action_content=action_content
        )
        returnValue([self.to_python_values(sms) for sms in response.get('sms')])
        
    @inlineCallbacks
    def delete_message(self, sms_id):
        """
        Delete New Messages for a user
        
        Arguments:
        
        sms_id --   the id of the sms to be deleted
        
        """
        session_id = yield self.get_session_id()
        response = yield self.connection.deletenewmessages(
            api_sessionid=session_id,
            action_content={
                'sms_id': sms_id
            }
        )
        returnValue(response.get('status'))

    @inlineCallbacks
    def send_messages(self, messages):
        """
        Send Sms Messages
        
        Arguments:
        
        messages -- A list of messages to be sent. Each message is a dictionary.
        
        The dictionary's key values match the XML element names of the Foneworx
        XML API:
        
        -- Manditory 
            <msisdn> - number(s) to send the message to, delimited by ~ (tilde)
            <message> - message to be sent
        -- Allowed Characters: See General Notes
        -- Optional 
            <rule> - which rule to link the message to 
            <send_at> - when to send the sms (yyyy-mm-dd HH:MM:SS)
        -- Optional - Please do not specify these, unless you have been given the correct values by foneworx
            <source_addr> - the number the message is sent from (only works if you also specify <sentby>)
            <sentby> - the bind/account to use to send the message 
            <smstype> - 0 for normal text sms, 64 for encoded sms, and then message has to contain the hex string
        
        """
        session_id = yield self.get_session_id()
        response = yield self.connection.sendmessages(
            api_sessionid=session_id,
            action_content={
                "sms": messages
            }
        )
        returnValue(response.get('sms'))
    
    @inlineCallbacks
    def sent_messages(self, **options):
        """
        Get Status Updates For Sent Messages
        
        Keyword arguments:
        
        smstime --  if smstime is empty the system will only return new messages 
                    since the last time of this call for this user. if smstime 
                    (format yyyymmddHHMMSS) is filled in, it will return all 
                    message since that time
        
        give_detail --  if you want the message and the destination numbers 
                        returned for each sms (1) - true (0) - false
        
        """
        session_id = yield self.get_session_id()
        response = yield self.connection.sentmessages(
            api_sessionid=session_id,
            action_content=options
        )
        returnValue([self.to_python_values(sms) for sms in response.get('sms')])
    
    @inlineCallbacks
    def delete_sent_messages(self, sms_id):
        """
        Delete a Sent Message
        
        Arguments:
        
        sms_id -- the id of the sms
        
        """
        session_id = yield self.get_session_id()
        response = yield self.connection.deletesentmessages(
            api_sessionid=session_id,
            action_content={
                'sms_id': sms_id
            }
        )
        returnValue(response.get('status'))
