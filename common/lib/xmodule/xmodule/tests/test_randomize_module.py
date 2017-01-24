"""
Test cases covering workflows and behaviors for the Randomize XModule
"""
import unittest
from datetime import datetime, timedelta

from django.utils.timezone import UTC
from opaque_keys.edx.locator import BlockUsageLocator
from xblock.fields import ScopeIds
from xmodule.randomize_module import RandomizeModule

from .test_course_module import DummySystem as DummyImportSystem


ORG = 'test_org'
COURSE = 'test_course'

START = '2013-01-01T01:00:00'
_TODAY = datetime.now(UTC())
_LAST_WEEK = _TODAY - timedelta(days=7)
_NEXT_WEEK = _TODAY + timedelta(days=7)


class RandomizeModuleTestCase(unittest.TestCase):
    """Make sure the randomize module works"""

    def setUp(self):
        """
        Initialize dummy testing course.
        """
        super(RandomizeModuleTestCase, self).setUp()
        self.system = DummyImportSystem(load_error_modules=True)
        self.system.seed = None
        self.course = self.get_dummy_course()
        self.modulestore = self.system.modulestore

    def get_dummy_course(self, start=_TODAY):
        """Get a dummy course"""

        self.start_xml = '''
         <course org="{org}" course="{course}"
                graceperiod="1 day" url_name="test"
                start="{start}">
            <chapter url="ch1" url_name="chapter1" display_name="CH1">
                <randomize url_name="my_randomize">
                <html url_name="a" display_name="A">Two houses, ...</html>
                <html url_name="b" display_name="B">Three houses, ...</html>
                </randomize>
            </chapter>
            <chapter url="ch2" url_name="chapter2" display_name="CH2">
            </chapter>
         </course>
         '''.format(org=ORG, course=COURSE, start=start)

        return self.system.process_xml(self.start_xml)

    def test_import(self):
        """
        Just make sure descriptor loads without error
        """
        self.get_dummy_course(START)

    def test_course_has_started(self):
        """
        Test CourseDescriptor.has_started.
        """
        self.course.start = _LAST_WEEK
        self.assertTrue(self.course.has_started())
        self.course.start = _NEXT_WEEK
        self.assertFalse(self.course.has_started())

    def test_children(self):
        """ Check course/randomize module works fine """

        self.assertTrue(self.course.has_children)
        self.assertEquals(len(self.course.get_children()), 2)

        def inner_get_module(descriptor):
            """
            Override systems.get_module
                This method will be called when any call is made to self.system.get_module
            """
            if isinstance(descriptor, BlockUsageLocator):
                location = descriptor
                descriptor = self.modulestore.get_item(location, depth=None)
            descriptor.xmodule_runtime = self.get_dummy_course()
            descriptor.xmodule_runtime.descriptor_runtime = descriptor._runtime  # pylint: disable=protected-access
            descriptor.xmodule_runtime.get_module = inner_get_module
            return descriptor

        self.system.get_module = inner_get_module

        # Get randomize_descriptor from the course & verify its children
        randomize_descriptor = inner_get_module(self.course.id.make_usage_key('randomize', 'my_randomize'))
        self.assertTrue(randomize_descriptor.has_children)
        self.assertEquals(len(randomize_descriptor.get_children()), 2)

        # Call RandomizeModule which will select an element from the list of available items
        randomize_module = RandomizeModule(
            randomize_descriptor,
            self.system,
            scope_ids=ScopeIds(None, None, self.course.id, self.course.id)
        )

        # Verify the selected child
        self.assertEquals(len(randomize_module.get_child_descriptors()), 1, "No child is chosen")
        self.assertIn(randomize_module.child.display_name, ['A', 'B'], "Unwanted child selected")
