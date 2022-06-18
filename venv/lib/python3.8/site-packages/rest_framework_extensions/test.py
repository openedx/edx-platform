# Leaving this module here for backwards compatibility but this is just proxy
# for rest_framework.test

import warnings

from rest_framework.test import (
    force_authenticate,
    APIRequestFactory,
    ForceAuthClientHandler,
    APIClient,
    APITransactionTestCase,
    APITestCase
)


__all__ = (
    'force_authenticate,'
    'APIRequestFactory,'
    'ForceAuthClientHandler,'
    'APIClient,'
    'APITransactionTestCase,'
    'APITestCase'
)

warnings.warn(
    'Use of this module is deprecated! Use rest_framework.test instead.',
    DeprecationWarning
)
