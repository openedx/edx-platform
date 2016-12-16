# -*- coding: utf-8 -*-
""" Test settings for Docker-based devstack. """

import os

os.environ['EDXAPP_TEST_MONGO_HOST'] = os.environ.get('EDXAPP_TEST_MONGO_HOST', 'edx.devstack.mongo')

# noinspection PyUnresolvedReferences
from .test import *  # pylint: disable=wildcard-import
