#pylint: disable=missing-docstring

import ddt
from django.test import TestCase

from openedx.core.djangoapps.api_admin.forms import ApiAccessRequestForm
from openedx.core.djangoapps.api_admin.tests.utils import VALID_DATA
from openedx.core.djangolib.testing.utils import skip_unless_lms


@skip_unless_lms
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
