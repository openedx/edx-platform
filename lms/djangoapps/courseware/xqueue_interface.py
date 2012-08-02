#
#  LMS Interface to external queueing system (xqueue)
#
import json
import requests

# TODO: Collection of parameters to be hooked into rest of edX system
XQUEUE_LMS_AUTH = ('LMS','PaloAltoCA') # (username, password)
XQUEUE_SUBMIT_URL = 'http://xqueue.edx.org'

def upload_files_to_s3():
    print '  THK: xqueue_interface.upload_files_to_s3'


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


def send_to_queue(header, body, xqueue_url=None):
    '''
    Submit a request to xqueue.
    
    header: JSON-serialized dict in the format described in 'xqueue_interface.make_xheader'

    body: Serialized data for the receipient behind the queueing service. The operation of
            xqueue is agnostic to the contents of 'body'

    Returns an 'error' flag indicating error in xqueue transaction
    '''
    if xqueue_url is None:
        xqueue_url = XQUEUE_SUBMIT_URL

    # First, we login with our credentials
    #------------------------------------------------------------
    s = requests.session()
    try:
        r = s.post(xqueue_url+'/xqueue/login/', data={ 'username': XQUEUE_LMS_AUTH[0],
                                                       'password': XQUEUE_LMS_AUTH[1] })
    except Exception as err:
        msg = 'Error in xqueue_interface.send_to_queue %s: Cannot connect to server url=%s' % (err, xqueue_url)
        raise Exception(msg)

    # Xqueue responses are JSON-serialized dicts
    xreply = json.loads(r.text)
    return_code = xreply['return_code']
    if return_code: # Nonzero return code from xqueue indicates error
        print '  Error in queue_interface.send_to_queue: %s' % xreply['content']
        return 1 # Error

    # Next, we can make a queueing request
    #------------------------------------------------------------
    payload = {'xqueue_header': header,
               'xqueue_body'  : body}
    try:
        # Send request
        r = s.post(xqueue_url+'/xqueue/submit/', data=payload)
    except Exception as err:
        msg = 'Error in xqueue_interface.send_to_queue %s: Cannot connect to server url=%s' % (err, xqueue_url)
        raise Exception(msg)

    xreply = json.loads(r.text)
    return_code = xreply['return_code']
    if return_code:
        print '  Error in queue_interface.send_to_queue: %s' % xreply['content']

    return return_code
