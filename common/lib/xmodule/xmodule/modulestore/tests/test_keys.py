import ddt

from unittest import TestCase
from opaque_keys import InvalidKeyError
from xmodule.modulestore.locations import Location, SlashSeparatedCourseKey

class TestAssetKey(TestCase):
    """
    Test Asset Key
    """

