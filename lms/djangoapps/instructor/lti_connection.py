"""
Send grades to an OpenEdX LTI component
"""
import base64
import hashlib
import json
import urllib

from oauthlib.oauth1 import Client  # pylint: disable=F0401
import requests
from oauthlib.common import Request


def validate_lti_passport(key, secret, url):
    """
    Sanity-check LTI passport credentials
    """
    response = _send_lti_2_json_request('GET', url, key, secret)
    return response.status_code == 200


def post_grade(url_base, key, secret, grade_row):
    """
    Post a grade to the LTI endpoint
    """
    uid, anon_id, email, grade, total, comment = grade_row

    if total == 0 or anon_id == '':
        return (False, uid, email)

    url = url_base + anon_id
    payload = {
        '@context': 'http://purl.imsglobal.org/ctx/lis/v2/Result',
        '@type': 'Result',
        'comment': comment,
        'resultScore': grade / total,
    }
    response = _send_lti_2_json_request(
        'PUT',
        url,
        key,
        secret,
        data=json.dumps(payload),
    )
    if response.status_code != 200:
        return (False, uid, email)
    else:
        return (True, uid, email)


def _send_lti_2_json_request(method, url, key, secret, data=None):
    """
    Issue a session-based LTI request
    """
    session = requests.Session()
    request = requests.Request(method, url, data=data)
    request.headers.update({
        'Content-Type': 'application/vnd.ims.lis.v2.result+json',
    })
    request_prepared = session.prepare_request(request)
    auth_header_val = _get_authorization_header(request_prepared, key, secret)
    request.headers.update({
        'Authorization': auth_header_val,
    })
    request_prepared_authorized = session.prepare_request(request)
    response = session.send(request_prepared_authorized)
    return response


def _get_authorization_header(request, client_key, client_secret):
    """
    Get proper HTTP Authorization header for a given request

    Arguments:
        request: Request object to log Authorization header for

    Returns:
        authorization header
    """
    sha1 = hashlib.sha1()
    body = request.body or ''
    sha1.update(body)
    oauth_body_hash = unicode(base64.b64encode(
        sha1.digest()  # pylint: disable=too-many-function-args
    ))
    client = Client(client_key, client_secret)
    params = client.get_oauth_params(None)
    params.append((u'oauth_body_hash', oauth_body_hash))

    blank_request = Request(urllib.unquote(request.url), http_method=request.method, body='', headers=request.headers, encoding='utf_8')
    blank_request.oauth_params = params
    blank_request.decoded_body = ''

    signature = client.get_oauth_signature(blank_request)
    blank_request.oauth_params.append((u'oauth_signature', signature))
    headers = client._render(  # pylint: disable=protected-access
        blank_request
    )[1]
    return headers['Authorization']
