"""
Edly factories for management commands.
"""
import factory
from factory.django import DjangoModelFactory
from provider.constants import CONFIDENTIAL
from provider.oauth2.models import Client


class ClientFactory(DjangoModelFactory):
    """
    Factory for model client.
    """
    class Meta(object):
        model = Client

    name = 'example.com'
    client_id = factory.Sequence(u'client_{0}'.format)
    client_secret = 'some_secret'
    client_type = CONFIDENTIAL

    url = 'http://example.com'
    redirect_uri = 'http://example.com/oidc'
