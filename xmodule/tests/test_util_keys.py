"""
Tests for xmodule/util/keys.py
"""
import ddt
from unittest import TestCase
from unittest.mock import Mock

from opaque_keys.edx.locator import BlockUsageLocator
from opaque_keys.edx.keys import CourseKey
from xmodule.util.keys import BlockKey, derive_key


mock_block = Mock()
mock_block.id = CourseKey.from_string('course-v1:Beeper+B33P+BOOP')

derived_key_scenarios = [
    {
        'source': BlockUsageLocator.from_string(
            'block-v1:edX+DemoX+Demo_Course+type@chapter+block@interactive_demonstrations'
        ),
        'parent': mock_block,
        'expected': BlockKey('chapter', '5793ec64e25ed870a7dd'),
    },
    {
        'source': BlockUsageLocator.from_string(
            'block-v1:edX+DemoX+Demo_Course+type@chapter+block@interactive_demonstrations'
        ),
        'parent': BlockKey('chapter', 'thingy'),
        'expected': BlockKey('chapter', '599792a5622d85aa41e6'),
    }
]


@ddt.ddt
class TestDeriveKey(TestCase):
    """
    Test reproducible block ID generation.
    """
    @ddt.data(*derived_key_scenarios)
    @ddt.unpack
    def test_derive_key(self, source, parent, expected):
        """
        Test that derive_key returns the expected value.
        """
        assert derive_key(source, parent) == expected
