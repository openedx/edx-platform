"""
OpenStack OpenId backend
"""
from urllib.parse import urlsplit

from openid.extensions import ax

from .open_id import OpenIdAuth


class OpenStackOpenId(OpenIdAuth):
    name = 'openstack'
    URL = 'openstackid.org'

    def get_user_details(self, response):
        """Generate username from identity url"""
        values = super().get_user_details(response)
        values['username'] = values.get('username') or \
            urlsplit(response.identity_url).path.strip('/')
        values['nickname'] = values.get('nickname', '')
        return values

    def setup_request(self, params=None):
        """Fetch email, firstname, lastname from openid"""
        request = self.openid_request(params)

        # TODO: use sreg instead ax request to fetch nickname as username
        fetch_request = ax.FetchRequest()
        fetch_request.add(ax.AttrInfo(
            'http://axschema.org/contact/email',
            alias='email',
            required=True
        ))

        fetch_request.add(ax.AttrInfo(
            'http://axschema.org/namePerson/first',
            alias='firstname',
            required=True
        ))

        fetch_request.add(ax.AttrInfo(
            'http://axschema.org/namePerson/last',
            alias='lastname',
            required=True
        ))

        request.addExtension(fetch_request)
        return request
