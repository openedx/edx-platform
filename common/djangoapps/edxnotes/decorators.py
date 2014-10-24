import jwt
import datetime
from uuid import uuid4
from edxmako.shortcuts import render_to_string


# Replace these with your details
CONSUMER_KEY = 'yourconsumerkey'
CONSUMER_SECRET = 'yourconsumersecret'
DEFAULT_TTL = 86400


def _now():
    return datetime.datetime.utcnow().replace(microsecond=0)


def get_prefix():
    return '/edxnotes/api'


def get_token_url():
    return '/edxnotes/token'


def get_user_id():
    return 'edx_user'


def generate_uid():
    return uuid4().int


def generate_token():
    """
    Generetes token.
    """
    return jwt.encode({
        'd': {
            'consumerKey': 'consumerKey',
            'userId': 'edx_user',
            'issuedAt': _now().isoformat() + 'Z',
            'ttl': DEFAULT_TTL,
        },
    }, CONSUMER_SECRET)


def EdxNotes(cls):
    """
    Docstring for the decorator.
    """
    original_get_html = cls.get_html

    def get_html(self, *args, **kargs):
        return render_to_string('edxnotes_wrapper.html', {
            'content': original_get_html(self, *args, **kargs),
            'token': generate_token(),
            'prefix': get_prefix(),
            'token_url': get_token_url(),
            'user': get_user_id(),
            'uid': generate_uid(),
        })

    cls.get_html = get_html
    return cls
