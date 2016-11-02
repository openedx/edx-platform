"""
This file contains a function used to retrieve the token for the annotation backend
without having to create a view, but just returning a string instead.

It can be called from other files by using the following:
from xmodule.annotator_token import retrieve_token
"""
import datetime
from firebase_token_generator import create_token


def retrieve_token(userid, secret):
    '''
    Return a token for the backend of annotations.
    It uses the course id to retrieve a variable that contains the secret
    token found in inheritance.py. It also contains information of when
    the token was issued. This will be stored with the user along with
    the id for identification purposes in the backend.
    '''

    # the following five lines of code allows you to include the default timezone in the iso format
    # for more information: http://stackoverflow.com/questions/3401428/how-to-get-an-isoformat-datetime-string-including-the-default-timezone
    dtnow = datetime.datetime.now()
    dtutcnow = datetime.datetime.utcnow()
    delta = dtnow - dtutcnow
    newhour, newmin = divmod((delta.days * 24 * 60 * 60 + delta.seconds + 30) // 60, 60)
    newtime = "%s%+02d:%02d" % (dtnow.isoformat(), newhour, newmin)
    # uses the issued time (UTC plus timezone), the consumer key and the user's email to maintain a
    # federated system in the annotation backend server
    custom_data = {"issuedAt": newtime, "consumerKey": secret, "userId": userid, "ttl": 86400}
    newtoken = create_token(secret, custom_data)
    return newtoken
