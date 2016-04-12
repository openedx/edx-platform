#pylint: disable=missing-docstring
import unittest

import ddt
from django.conf import settings
from django.test import TestCase

from openedx.core.djangoapps.api_admin.forms import ApiAccessRequestForm
from openedx.core.djangoapps.api_admin.tests.utils import VALID_DATA


@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
@ddt.ddt
class ApiAccessFormTest(TestCase):

    @ddt.data(
        (VALID_DATA, True),
        ({}, False),
        (dict(VALID_DATA, terms_of_service=False), False)
    )
    @ddt.unpack
    def test_form_valid(self, data, is_valid):
        form = ApiAccessRequestForm(data)
        self.assertEqual(form.is_valid(), is_valid)
