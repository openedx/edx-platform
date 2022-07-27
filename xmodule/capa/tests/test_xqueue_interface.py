# -*- coding: utf-8 -*-
"""
Tests the xqueue service interface.
"""

from unittest import TestCase
from django.conf import settings

from xmodule.capa.xqueue_interface import XQueueInterface, XQueueService


class XQueueServiceTest(TestCase):
    """
    Tests the XQueue service methods.
    """
    @staticmethod
    def construct_callback(*args, **kwargs):
        return 'https://lms.url/callback'

    def setUp(self):
        super().setUp()
        self.service = XQueueService(
            url=settings.XQUEUE_INTERFACE['url'],
            django_auth=settings.XQUEUE_INTERFACE['django_auth'],
            basic_auth=settings.XQUEUE_INTERFACE['basic_auth'],
            construct_callback=self.construct_callback,
            default_queuename='my-very-own-queue',
            waittime=settings.XQUEUE_WAITTIME_BETWEEN_REQUESTS,
        )

    def test_interface(self):
        assert isinstance(self.service.interface, XQueueInterface)

    def test_construct_callback(self):
        assert self.service.construct_callback() == 'https://lms.url/callback'

    def test_default_queuename(self):
        assert self.service.default_queuename == 'my-very-own-queue'

    def test_waittime(self):
        assert self.service.waittime == 5
