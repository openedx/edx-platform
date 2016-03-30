"""
Dummy factories for tests
"""
from factory.django import DjangoModelFactory
from openedx.core.djangoapps.ccxcon.models import CCXCon


class CcxConFactory(DjangoModelFactory):
    """
    Model factory for the CCXCon model
    """
    class Meta(object):
        model = CCXCon

    oauth_client_id = 'asdfjasdljfasdkjffsdfjksd98fsd8y24fdsiuhsfdsf'
    oauth_client_secret = '19123084091238901912308409123890'
    title = 'title for test ccxcon'
