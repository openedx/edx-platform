#
#  LMS Interface to external queueing system (xqueue)
#
import hashlib
import json
import logging
import requests
import time

# TODO: Collection of parameters to be hooked into rest of edX system
XQUEUE_LMS_AUTH = { 'username': 'LMS',
                    'password': 'PaloAltoCA' }
XQUEUE_URL = 'http://xqueue.edx.org'

log = logging.getLogger('mitx.' + __name__)

def make_hashkey(seed=None):
    '''
    Generate a string key by hashing 
    '''
    h = hashlib.md5()
    if seed is not None:
        h.update(str(seed))
    h.update(str(time.time()))
    return h.hexdigest()


def make_xheader(lms_callback_url, lms_key, queue_name):
    '''
    Generate header for delivery and reply of queue request.

    Xqueue header is a JSON-serialized dict:
        { 'lms_callback_url': url to which xqueue will return the request (string),
          'lms_key': secret key used by LMS to protect its state (string), 
          'queue_name': designate a specific queue within xqueue server, e.g. 'MITx-6.00x' (string)
        }
    '''
    return json.dumps({ 'lms_callback_url': lms_callback_url,
                        'lms_key': lms_key,
                        'queue_name': queue_name })


def parse_xreply(xreply):
    '''
    Parse the reply from xqueue. Messages are JSON-serialized dict:
        { 'return_code': 0 (success), 1 (fail)
          'content': Message from xqueue (string)
        }
    '''
    xreply = json.loads(xreply)
    return_code = xreply['return_code']
    content = xreply['content']
    return (return_code, content)


class XqueueInterface:
    '''
    Interface to the external grading system
    '''

    def __init__(self, url=XQUEUE_URL, auth=XQUEUE_LMS_AUTH):
        self.url  = url
        self.auth = auth
        self.s = requests.session()
        self._login()
        
    def send_to_queue(self, header, body, file_to_upload=None):
        '''
        Submit a request to xqueue.
        
        header: JSON-serialized dict in the format described in 'xqueue_interface.make_xheader'

        body: Serialized data for the receipient behind the queueing service. The operation of
                xqueue is agnostic to the contents of 'body'

        file_to_upload: File object to be uploaded to xqueue along with queue request

        Returns (error_code, msg) where error_code != 0 indicates an error
        '''
        # Attempt to send to queue
        (error, msg) = self._send_to_queue(header, body, file_to_upload)

        if error and (msg == 'login_required'): # Log in, then try again
            self._login()
            (error, msg) = self._send_to_queue(header, body, file_to_upload)

        return (error, msg)

    def _login(self):
        try:
            r = self.s.post(self.url+'/xqueue/login/', data={ 'username': self.auth['username'],
                                                              'password': self.auth['password'] })
        except requests.exceptions.ConnectionError, err:
            log.error(err)
            return (1, 'cannot connect to server') 

        return parse_xreply(r.text)

    def _send_to_queue(self, header, body, file_to_upload=None):

        payload = {'xqueue_header': header,
                   'xqueue_body'  : body}

        files = None
        if file_to_upload is not None:
            files = { file_to_upload.name: file_to_upload }

        try:
            r = self.s.post(self.url+'/xqueue/submit/', data=payload, files=files)
        except requests.exceptions.ConnectionError, err:
            log.error(err)
            return (1, 'cannot connect to server') 

        return parse_xreply(r.text)
