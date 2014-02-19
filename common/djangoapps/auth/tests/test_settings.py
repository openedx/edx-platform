"""
Tests settings across configurations.
"""

import functools

from django.conf import settings
from django.test import TestCase


def with_feature(key):
    """Decorator that runs `test_fn` iff settings.FEATURES has `key`.

    @with_feature('foo')
    def test_bar(...):

    means test_bar will execute if settings.FEATURES['foo'] is present, whether
    settings.FEATURES.get('foo') is truthy or falsy. This lets us declare our
    constraint in the signature rather that with boilerplate in each test body.

    `key` is a string matching a key in settings.FEATURES.

    Returns a wrapped version of `test_fn`.
    """

    # Silence missing docstring complaints for inner functions.
    # pylint: disable-msg=missing-docstring
    def guarded_test_fn(test_fn):

        # Test method names must start with test_ for test reporting and
        # discovery, so use wraps rather than returning a naked function.
        @functools.wraps(test_fn)
        def guard(*args, **kwargs):
            if key in settings.FEATURES:
                test_fn(*args, **kwargs)

        return guard

    return guarded_test_fn


class TestCommonSettings(TestCase):
    """Tests settings from lms/envs/common.py."""

    @with_feature('ENABLE_THIRD_PARTY_AUTH')
    def test_enable_third_party_auth_is_disabled(self):
        self.assertIs(
            False, settings.FEATURES.get('ENABLE_THIRD_PARTY_AUTH'))
