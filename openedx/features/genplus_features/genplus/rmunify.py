from hashlib import sha1
from django.conf import settings
import requests
import base64
import hmac
from datetime import datetime


class RmUnify:
    ORGANISATION = 'organisation'
    TEACHING_GROUP = 'teachinggroup'
    REGISTRATION_GROUP = 'registrationgroup'

    def __init__(self):
        self.key = settings.RM_UNIFY_KEY
        self.secret = settings.RM_UNIFY_SECRET

    def fetch(self, source, source_id):
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        # t = base64.b64encode(secret.encode())
        headers = {"Authorization": "Unify " + timestamp + ":" + self.hashed}
        url = self.generate_url(source, source_id)
        r = requests.get(url, headers=headers)
        print(r.json())

    @property
    def hashed(self):
        hashed = hmac.new(bytes(self.secret, 'utf-8'), bytes(d, 'utf-8'), sha1).digest()
        hashed = str(base64.urlsafe_b64encode(hashed), "UTF-8")
        hashed = hashed.replace('-', '+')
        return hashed.replace('_', '/')

    @staticmethod
    def generate_url(source, source_id):
        url = settings.RM_UNIFY_URL
        if source:
            url = url + source
        if source_id:
            url = url + source_id
        return url
