"""
Define test configuration for modulestores.
"""

from xmodule.modulestore.tests.django_utils import studio_store_config
from django.conf import settings

TEST_MODULESTORE = studio_store_config(settings.TEST_ROOT / "data")
