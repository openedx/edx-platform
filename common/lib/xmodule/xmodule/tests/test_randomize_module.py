import unittest

from .test_course_module import DummySystem as DummyImportSystem

ORG = 'test_org'
COURSE = 'test_course'

START = '2013-01-01T01:00:00'


class RandomizeModuleTestCase(unittest.TestCase):
    """Make sure the randomize module works"""
    @staticmethod
    def get_dummy_course(start):
        """Get a dummy course"""

        system = DummyImportSystem(load_error_modules=True)

        def to_attrb(n, v):
            return '' if v is None else '{0}="{1}"'.format(n, v).lower()

        start_xml = '''
         <course org="{org}" course="{course}"
                graceperiod="1 day" url_name="test"
                start="{start}"
                >
            <chapter url="hi" url_name="ch" display_name="CH">
                <randomize url_name="my_randomize">
                <html url_name="a" display_name="A">Two houses, ...</html>
                <html url_name="b" display_name="B">Three houses, ...</html>
                </randomize>
            </chapter>
         </course>
         '''.format(org=ORG, course=COURSE, start=start)

        return system.process_xml(start_xml)

    def test_import(self):
        """
        Just make sure descriptor loads without error
        """
        descriptor = self.get_dummy_course(START)

    # TODO: add tests that create a module and check.  Passing state is a good way to
    # check that child access works...
