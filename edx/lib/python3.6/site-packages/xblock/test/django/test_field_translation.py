"""
Test the case when a lazily-translated string is given as a default for
an XBlock String field.
"""

from __future__ import absolute_import, division, print_function, unicode_literals

import warnings

from django.test import TestCase
from django.utils import translation
from django.utils.translation import ugettext_lazy as _  # pylint: disable=import-error
from mock import Mock
from six import text_type

from xblock.core import XBlock
from xblock.fields import FailingEnforceTypeWarning, Scope, String, ScopeIds
from xblock.runtime import (
    DictKeyValueStore,
    KvsFieldData,
)
from xblock.test.tools import TestRuntime


class TestXBlockStringFieldDefaultTranslation(TestCase):
    """
    Tests for an XBlock String field with a lazily-translated default value.
    """
    def test_lazy_translation(self):
        with warnings.catch_warnings(record=True) as caught_warnings:
            warnings.simplefilter('always', FailingEnforceTypeWarning)

            class XBlockTest(XBlock):
                """
                Set up a class that contains a single string field with a translated default.
                """
                STR_DEFAULT_ENG = 'ENG: String to be translated'
                str_field = String(scope=Scope.settings, default=_('ENG: String to be translated'))

        # No FailingEnforceTypeWarning should have been triggered
        assert not caught_warnings

        # Construct a runtime and an XBlock using it.
        key_store = DictKeyValueStore()
        field_data = KvsFieldData(key_store)
        runtime = TestRuntime(Mock(), services={'field-data': field_data})

        # Change language to 'de'.
        user_language = 'de'
        with translation.override(user_language):
            tester = runtime.construct_xblock_from_class(XBlockTest, ScopeIds('s0', 'XBlockTest', 'd0', 'u0'))

            # Assert instantiated XBlock str_field value is not yet evaluated.
            assert 'django.utils.functional.' in str(type(tester.str_field))

            # Assert str_field *is* translated when the value is used.
            assert text_type(tester.str_field) == 'DEU: Translated string'
