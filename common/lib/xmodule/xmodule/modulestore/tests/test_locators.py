"""
Tests for opaque_keys.edx.locator.
"""
from unittest import TestCase

import random
from bson.objectid import ObjectId
from opaque_keys import InvalidKeyError
from opaque_keys.edx.locator import Locator, CourseLocator, BlockUsageLocator, DefinitionLocator
from ddt import ddt, data
from opaque_keys.edx.keys import UsageKey, CourseKey, DefinitionKey


@ddt
class LocatorTest(TestCase):
    """
    Tests for subclasses of Locator.
    """

    def test_cant_instantiate_abstract_class(self):
        self.assertRaises(TypeError, Locator)

    def test_course_constructor_underspecified(self):
        with self.assertRaises(InvalidKeyError):
            CourseLocator()
        with self.assertRaises(InvalidKeyError):
            CourseLocator(branch='published')

    def test_course_constructor_bad_version_guid(self):
        with self.assertRaises(ValueError):
            CourseLocator(version_guid="012345")

        with self.assertRaises(InvalidKeyError):
            CourseLocator(version_guid=None)

    def test_course_constructor_version_guid(self):
        # generate a random location
        test_id_1 = ObjectId()
        test_id_1_loc = str(test_id_1)
        testobj_1 = CourseLocator(version_guid=test_id_1)
        self.check_course_locn_fields(testobj_1, version_guid=test_id_1)
        self.assertEqual(str(testobj_1.version_guid), test_id_1_loc)
        self.assertEqual(testobj_1._to_string(), u'+'.join((testobj_1.VERSION_PREFIX, test_id_1_loc)))

        # Test using a given string
        test_id_2_loc = '519665f6223ebd6980884f2b'
        test_id_2 = ObjectId(test_id_2_loc)
        testobj_2 = CourseLocator(version_guid=test_id_2)
        self.check_course_locn_fields(testobj_2, version_guid=test_id_2)
        self.assertEqual(str(testobj_2.version_guid), test_id_2_loc)
        self.assertEqual(testobj_2._to_string(), u'+'.join((testobj_2.VERSION_PREFIX, test_id_2_loc)))

    @data(
        ' mit.eecs',
        'mit.eecs ',
        CourseLocator.VERSION_PREFIX + '+mit.eecs',
        BlockUsageLocator.BLOCK_PREFIX + '+black+mit.eecs',
        'mit.ee cs',
        'mit.ee,cs',
        'mit.ee+cs',
        'mit.ee&cs',
        'mit.ee()cs',
        CourseLocator.BRANCH_PREFIX + '+this',
        'mit.eecs+' + CourseLocator.BRANCH_PREFIX,
        'mit.eecs+' + CourseLocator.BRANCH_PREFIX + '+this+' + CourseLocator.BRANCH_PREFIX + '+that',
        'mit.eecs+' + CourseLocator.BRANCH_PREFIX + '+this+' + CourseLocator.BRANCH_PREFIX,
        'mit.eecs+' + CourseLocator.BRANCH_PREFIX + '+this ',
        'mit.eecs+' + CourseLocator.BRANCH_PREFIX + '+th%is ',
    )
    def test_course_constructor_bad_package_id(self, bad_id):
        """
        Test all sorts of badly-formed package_ids (and urls with those package_ids)
        """
        with self.assertRaises(InvalidKeyError):
            CourseLocator(org=bad_id, offering='test')

        with self.assertRaises(InvalidKeyError):
            CourseLocator(org='test', offering=bad_id)

        with self.assertRaises(InvalidKeyError):
            CourseKey.from_string('course-locator:test+{}'.format(bad_id))

    @data('course-locator:', 'course-locator:/mit.eecs', 'http:mit.eecs', 'course-locator//mit.eecs')
    def test_course_constructor_bad_url(self, bad_url):
        with self.assertRaises(InvalidKeyError):
            CourseKey.from_string(bad_url)

    def test_course_constructor_url(self):
        # Test parsing a url when it starts with a version ID and there is also a block ID.
        # This hits the parsers parse_guid method.
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = CourseKey.from_string("course-locator:{}+{}+{}+hw3".format(
            CourseLocator.VERSION_PREFIX, test_id_loc, CourseLocator.BLOCK_PREFIX
        ))
        self.check_course_locn_fields(
            testobj,
            version_guid=ObjectId(test_id_loc)
        )

    def test_course_constructor_url_package_id_and_version_guid(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = CourseKey.from_string(
            'course-locator:mit.eecs+honors.6002x+{}+{}'.format(CourseLocator.VERSION_PREFIX, test_id_loc)
        )
        self.check_course_locn_fields(
            testobj,
            org='mit.eecs',
            offering='honors.6002x',
            version_guid=ObjectId(test_id_loc)
        )

    def test_course_constructor_url_package_id_branch_and_version_guid(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        org = 'mit.eecs'
        offering = '~6002x'
        testobj = CourseKey.from_string('course-locator:{}+{}+{}+draft-1+{}+{}'.format(
            org, offering, CourseLocator.BRANCH_PREFIX, CourseLocator.VERSION_PREFIX, test_id_loc
        ))
        self.check_course_locn_fields(
            testobj,
            org=org,
            offering=offering,
            branch='draft-1',
            version_guid=ObjectId(test_id_loc)
        )

    def test_course_constructor_package_id_no_branch(self):
        org = 'mit.eecs'
        offering = '6002x'
        testurn = '{}+{}'.format(org, offering)
        testobj = CourseLocator(org=org, offering=offering)
        self.check_course_locn_fields(testobj, org=org, offering=offering)
        self.assertEqual(testobj._to_string(), testurn)

    def test_course_constructor_package_id_separate_branch(self):
        org = 'mit.eecs'
        offering = '6002x'
        test_branch = 'published'
        expected_urn = '{}+{}+{}+{}'.format(org, offering, CourseLocator.BRANCH_PREFIX, test_branch)
        testobj = CourseLocator(org=org, offering=offering, branch=test_branch)
        self.check_course_locn_fields(
            testobj,
            org=org,
            offering=offering,
            branch=test_branch,
        )
        self.assertEqual(testobj.branch, test_branch)
        self.assertEqual(testobj._to_string(), expected_urn)

    def test_block_constructor(self):
        expected_org = 'mit.eecs'
        expected_offering = '6002x'
        expected_branch = 'published'
        expected_block_ref = 'HW3'
        testurn = 'edx:{}+{}+{}+{}+{}+{}+{}+{}'.format(
            expected_org, expected_offering, CourseLocator.BRANCH_PREFIX, expected_branch,
            BlockUsageLocator.BLOCK_TYPE_PREFIX, 'problem', BlockUsageLocator.BLOCK_PREFIX, 'HW3'
        )
        testobj = UsageKey.from_string(testurn)
        self.check_block_locn_fields(
            testobj,
            org=expected_org,
            offering=expected_offering,
            branch=expected_branch,
            block_type='problem',
            block=expected_block_ref
        )
        self.assertEqual(unicode(testobj), testurn)
        testobj = testobj.for_version(ObjectId())
        agnostic = testobj.version_agnostic()
        self.assertIsNone(agnostic.version_guid)
        self.check_block_locn_fields(agnostic,
                                     org=expected_org,
                                     offering=expected_offering,
                                     branch=expected_branch,
                                     block=expected_block_ref)

    def test_block_constructor_url_version_prefix(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = UsageKey.from_string(
            'edx:mit.eecs+6002x+{}+{}+{}+problem+{}+lab2'.format(
                CourseLocator.VERSION_PREFIX, test_id_loc, BlockUsageLocator.BLOCK_TYPE_PREFIX, BlockUsageLocator.BLOCK_PREFIX
            )
        )
        self.check_block_locn_fields(
            testobj,
            org='mit.eecs',
            offering='6002x',
            block_type='problem',
            block='lab2',
            version_guid=ObjectId(test_id_loc)
        )
        agnostic = testobj.course_agnostic()
        self.check_block_locn_fields(
            agnostic,
            block='lab2',
            org=None,
            offering=None,
            version_guid=ObjectId(test_id_loc)
        )
        self.assertIsNone(agnostic.offering)
        self.assertIsNone(agnostic.org)

    def test_block_constructor_url_kitchen_sink(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = UsageKey.from_string(
            'edx:mit.eecs+6002x+{}+draft+{}+{}+{}+problem+{}+lab2'.format(
                CourseLocator.BRANCH_PREFIX, CourseLocator.VERSION_PREFIX, test_id_loc,
                BlockUsageLocator.BLOCK_TYPE_PREFIX, BlockUsageLocator.BLOCK_PREFIX
            )
        )
        self.check_block_locn_fields(
            testobj,
            org='mit.eecs',
            offering='6002x',
            branch='draft',
            block='lab2',
            version_guid=ObjectId(test_id_loc)
        )

    def test_colon_name(self):
        """
        It seems we used to use colons in names; so, ensure they're acceptable.
        """
        org = 'mit.eecs'
        offering = '1'
        branch = 'foo'
        block_id = 'problem:with-colon~2'
        testobj = BlockUsageLocator(
            CourseLocator(org=org, offering=offering, branch=branch),
            block_type='problem',
            block_id=block_id
        )
        self.check_block_locn_fields(
            testobj, org=org, offering=offering, branch=branch, block=block_id
        )

    def test_relative(self):
        """
        Test making a relative usage locator.
        """
        org = 'mit.eecs'
        offering = '1'
        branch = 'foo'
        baseobj = CourseLocator(org=org, offering=offering, branch=branch)
        block_id = 'problem:with-colon~2'
        testobj = BlockUsageLocator.make_relative(baseobj, 'problem', block_id)
        self.check_block_locn_fields(
            testobj, org=org, offering=offering, branch=branch, block=block_id
        )
        block_id = 'completely_different'
        testobj = BlockUsageLocator.make_relative(testobj, 'problem', block_id)
        self.check_block_locn_fields(
            testobj, org=org, offering=offering, branch=branch, block=block_id
        )

    def test_repr(self):
        testurn = u'edx:mit.eecs+6002x+{}+published+{}+problem+{}+HW3'.format(
            CourseLocator.BRANCH_PREFIX, BlockUsageLocator.BLOCK_TYPE_PREFIX, BlockUsageLocator.BLOCK_PREFIX
        )
        testobj = UsageKey.from_string(testurn)
        self.assertEqual("BlockUsageLocator(CourseLocator(u'mit.eecs', u'6002x', u'published', None), u'problem', u'HW3')", repr(testobj))

    def test_description_locator_url(self):
        object_id = '{:024x}'.format(random.randrange(16 ** 24))
        definition_locator = DefinitionLocator('html', object_id)
        self.assertEqual('defx:{}+{}+html'.format(object_id, DefinitionLocator.BLOCK_TYPE_PREFIX), unicode(definition_locator))
        self.assertEqual(definition_locator, DefinitionKey.from_string(unicode(definition_locator)))

    def test_description_locator_version(self):
        object_id = '{:024x}'.format(random.randrange(16 ** 24))
        definition_locator = DefinitionLocator('html', object_id)
        self.assertEqual(object_id, str(definition_locator.version()))

    # ------------------------------------------------------------------
    # Utilities

    def check_course_locn_fields(self, testobj, version_guid=None,
                                 org=None, offering=None, branch=None):
        """
        Checks the version, org, offering, and branch in testobj
        """
        self.assertEqual(testobj.version_guid, version_guid)
        self.assertEqual(testobj.org, org)
        self.assertEqual(testobj.offering, offering)
        self.assertEqual(testobj.branch, branch)

    def check_block_locn_fields(self, testobj, version_guid=None,
                                org=None, offering=None, branch=None, block_type=None, block=None):
        """
        Does adds a block id check over and above the check_course_locn_fields tests
        """
        self.check_course_locn_fields(testobj, version_guid, org, offering,
                                      branch)
        if block_type is not None:
            self.assertEqual(testobj.block_type, block_type)
        self.assertEqual(testobj.block_id, block)
