"""
Thorough tests of BlockUsageLocator, as well as UsageKeys generally
"""
from itertools import product

import ddt
import itertools  # pylint: disable=wrong-import-order
from bson.objectid import ObjectId

from opaque_keys import InvalidKeyError
from opaque_keys.edx.keys import UsageKey
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator, LocalId
from opaque_keys.edx.tests import LocatorBaseTest

# Pairs for testing the clean* functions.
# The first item in the tuple is the input string.
# The second item in the tuple is what the result of
# replacement should be.
GENERAL_PAIRS = [
    ('', ''),
    (' ', '_'),
    ('abc,', 'abc_'),
    ('ab    fg!@//\\aj', 'ab_fg_aj'),
    ("ab\xA9", "ab_"),  # no unicode allowed for now
]

# Block usage locator to use in tests.
TEST_ID_LOC = '519665f6223ebd6980884f2b'
BLOCK_URL = (
    f'block-v1:org+course+run+{CourseLocator.BRANCH_PREFIX}'
    f'@draft+{CourseLocator.VERSION_PREFIX}@{TEST_ID_LOC}'
    f'+{BlockUsageLocator.BLOCK_TYPE_PREFIX}'
    f'@problem+{BlockUsageLocator.BLOCK_PREFIX}@lab2'
)


@ddt.ddt
class TestBlockUsageLocators(LocatorBaseTest):
    """
    Tests of :class:`.BlockUsageLocator`
    """
    @ddt.data(
        f"block-v1:org+course+run+{BlockUsageLocator.BLOCK_TYPE_PREFIX}"
        f"@category+{BlockUsageLocator.BLOCK_PREFIX}@name",
        f"block-v1:org+course+run+{CourseLocator.BRANCH_PREFIX}"
        f"@revision+{BlockUsageLocator.BLOCK_TYPE_PREFIX}"
        f"@category+{BlockUsageLocator.BLOCK_PREFIX}@name",
        "i4x://org/course/category/name",
        "i4x://org/course/category/name@revision",
        # now try the extended char sets - we expect that "%" should be OK in deprecated-style ids,
        # but should not be valid in new-style ids
        f"block-v1:org.dept.sub-prof+course.num.section-4"
        f"+run.hour.min-99+{BlockUsageLocator.BLOCK_TYPE_PREFIX}"
        f"@category+{BlockUsageLocator.BLOCK_PREFIX}@name:12.33-44",
        "i4x://org.dept%sub-prof/course.num%section-4/category/name:12%33-44",
    )
    def test_string_roundtrip(self, url):
        self.assertEqual(
            url,
            str(UsageKey.from_string(url))
        )

    @ddt.data(
        ((), {
            'org': 'org',
            'course': 'course',
            'run': 'run',
            'category': 'category',
            'name': 'name',
        }, 'org', 'course', 'run', 'category', 'name', None),
        ((), {
            'org': 'org',
            'course': 'course',
            'run': 'run',
            'category': 'category',
            'name': 'name:more_name',
        }, 'org', 'course', 'run', 'category', 'name:more_name', None),
        (['org', 'course', 'run', 'category', 'name'], {}, 'org', 'course', 'run', 'category', 'name', None),
    )
    @ddt.unpack
    def test_valid_locations(self, args, kwargs, org, course, run, category, name, revision):  # pylint: disable=unused-argument
        course_key = CourseLocator(org=org, course=course, run=run, branch=revision, deprecated=True)
        locator = BlockUsageLocator(course_key, block_type=category, block_id=name, deprecated=True)
        self.assertEqual(org, locator.course_key.org)
        self.assertEqual(course, locator.course_key.course)
        self.assertEqual(run, locator.course_key.run)
        self.assertEqual(category, locator.block_type)
        self.assertEqual(name, locator.block_id)
        self.assertEqual(revision, locator.course_key.branch)

    @ddt.data(
        (("foo",), {}),
        (["foo", "bar"], {}),
        (["foo", "bar", "baz", "blat/blat", "foo"], {}),
        (["foo", "bar", "baz", "blat", "foo/bar"], {}),
        (["foo", "bar", "baz", "blat:blat", "foo:bar"], {}),  # ':' ok in name, not in category
        (('org', 'course', 'run', 'category', 'name with spaces', 'revision'), {}),
        (('org', 'course', 'run', 'category', 'name/with/slashes', 'revision'), {}),
        (('org', 'course', 'run', 'category', 'name', '\xae'), {}),
        (('org', 'course', 'run', 'category', '\xae', 'revision'), {}),
        ((), {
            'tag': 'tag',
            'course': 'course',
            'category': 'category',
            'name': 'name@more_name',
            'org': 'org'
        }),
        ((), {
            'tag': 'tag',
            'course': 'course',
            'category': 'category',
            'name': 'name ',   # extra space
            'org': 'org'
        }),
    )
    @ddt.unpack
    def test_invalid_locations(self, *args, **kwargs):
        with self.assertRaises(TypeError):
            BlockUsageLocator(*args, **kwargs)

    @ddt.data(
        ('a:b', 'a_b'),  # no colons in non-name components
        ('a-b', 'a-b'),  # dashes ok
        ('a.b', 'a.b'),  # dot ok
        *GENERAL_PAIRS
    )
    def test_clean(self, pair):
        self.assertEqual(BlockUsageLocator.clean(pair[0]), pair[1])

    @ddt.data(
        ('a:b', 'a:b'),  # colons ok in names
        ('a-b', 'a-b'),  # dashes ok in names
        ('a.b', 'a.b'),  # dot ok in names
        *GENERAL_PAIRS
    )
    def test_clean_for_url_name(self, pair):
        self.assertEqual(BlockUsageLocator.clean_for_url_name(pair[0]), pair[1])

    @ddt.data(
        ("a:b", "a_b"),   # no colons for html use
        ("a-b", "a-b"),   # dashes ok (though need to be replaced in various use locations. ugh.)
        ('a.b', 'a_b'),   # no dots.
        *GENERAL_PAIRS
    )
    def test_clean_for_html(self, pair):
        self.assertEqual(BlockUsageLocator.clean_for_html(pair[0]), pair[1])

    def test_html_id(self):
        course_key = CourseLocator('org', 'course', 'run')
        locator = BlockUsageLocator(course_key, block_type='cat', block_id='name:more_name')
        self.assertEqual(locator.html_id(), "name:more_name")

    def test_deprecated_html_id(self):
        course_key = CourseLocator('org', 'course', 'run', version_guid='rev', deprecated=True)
        locator = BlockUsageLocator(course_key, block_type='cat', block_id='name:more_name', deprecated=True)
        self.assertEqual(locator.html_id(), "i4x-org-course-cat-name_more_name-rev")

    @ddt.data(
        'course',
        'org',
        'run',
        'branch',
        'version_guid',
        'revision',
        'version',
        'block_id',
        'block_type',
        'name',
        'category'
    )
    def test_replacement(self, key):
        course_key = CourseLocator('org', 'course', 'run', 'rev', deprecated=True)
        kwargs = {key: 'newvalue'}
        self.assertEqual(
            getattr(BlockUsageLocator(course_key, 'c', 'n', deprecated=True).replace(**kwargs), key),
            'newvalue'
        )

        with self.assertRaises(InvalidKeyError):
            BlockUsageLocator(course_key, 'c', 'n', deprecated=True).replace(block_id='name\xae')

    @ddt.data('course_key', 'block_type', 'block_id')
    def test_immutable(self, attr):
        course_key = CourseLocator('org', 'course', 'run', 'rev', deprecated=True)
        loc = BlockUsageLocator(course_key, 'c', 'n')
        with self.assertRaises(AttributeError):
            setattr(loc, attr, attr)

    @ddt.data(*product((True, False), repeat=2))
    @ddt.unpack
    def test_map_into_course_location(self, deprecated_source, deprecated_dest):
        original_course = CourseLocator('org', 'course', 'run', deprecated=deprecated_source)
        new_course = CourseLocator('edX', 'toy', '2012_Fall', deprecated=deprecated_dest)
        loc = BlockUsageLocator(original_course, 'cat', 'name:more_name', deprecated=deprecated_source)
        expected = BlockUsageLocator(new_course, 'cat', 'name:more_name', deprecated=deprecated_dest)
        actual = loc.map_into_course(new_course)

        self.assertEqual(expected, actual)

    @ddt.data(
        (BlockUsageLocator, '_id.', 'i4x', (CourseLocator('org', 'course', 'run', 'rev', deprecated=True), 'ct', 'n')),
        (BlockUsageLocator, '', 'i4x', (CourseLocator('org', 'course', 'run', 'rev', deprecated=True), 'ct', 'n')),
    )
    @ddt.unpack
    def test_to_deprecated_son(self, key_cls, prefix, tag, source):
        source_key = key_cls(*source, deprecated=True)
        son = source_key.to_deprecated_son(prefix=prefix, tag=tag)
        self.assertEqual(son.keys(),
                         [prefix + key for key in ('tag', 'org', 'course', 'category', 'name', 'revision')])

        self.assertEqual(son[prefix + 'tag'], tag)
        self.assertEqual(son[prefix + 'org'], source_key.course_key.org)
        self.assertEqual(son[prefix + 'course'], source_key.course_key.course)
        self.assertEqual(son[prefix + 'category'], source_key.block_type)
        self.assertEqual(son[prefix + 'name'], source_key.block_id)
        self.assertEqual(son[prefix + 'revision'], source_key.course_key.branch)

    @ddt.data(
        (UsageKey.from_string('i4x://org/course/ct/n'), 'run'),
        (UsageKey.from_string('i4x://org/course/ct/n@rev'), 'run'),
    )
    @ddt.unpack
    def test_deprecated_son_roundtrip(self, key, run):
        self.assertEqual(
            key.replace(course_key=key.course_key.replace(run=run)),
            key.__class__._from_deprecated_son(key.to_deprecated_son(), run)  # pylint: disable=protected-access
        )

    def test_block_constructor(self):
        expected_org = 'mit.eecs'
        expected_course = '6002x'
        expected_run = '2014_T2'
        expected_branch = 'published'
        expected_block_ref = 'HW3'
        testurn = (
            f'block-v1:{expected_org}+{expected_course}+{expected_run}'
            f'+{CourseLocator.BRANCH_PREFIX}@{expected_branch}+'
            f'{BlockUsageLocator.BLOCK_TYPE_PREFIX}@problem+'
            f'{BlockUsageLocator.BLOCK_PREFIX}@HW3'
        )
        testobj = UsageKey.from_string(testurn)
        self.check_block_locn_fields(
            testobj,
            org=expected_org,
            course=expected_course,
            run=expected_run,
            branch=expected_branch,
            block_type='problem',
            block=expected_block_ref
        )
        self.assertEqual(str(testobj), testurn)
        testobj = testobj.for_version(ObjectId())
        agnostic = testobj.version_agnostic()
        self.assertIsNone(agnostic.version_guid)
        self.check_block_locn_fields(
            agnostic,
            org=expected_org,
            course=expected_course,
            run=expected_run,
            branch=expected_branch,
            block=expected_block_ref
        )

    def test_block_constructor_url_version_prefix(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = UsageKey.from_string(
            f'block-v1:mit.eecs+6002x+2014_T2+{CourseLocator.VERSION_PREFIX}'
            f'@{test_id_loc}+{BlockUsageLocator.BLOCK_TYPE_PREFIX}'
            f'@problem+{BlockUsageLocator.BLOCK_PREFIX}@lab2'
        )
        self.check_block_locn_fields(
            testobj,
            org='mit.eecs',
            course='6002x',
            run='2014_T2',
            block_type='problem',
            block='lab2',
            version_guid=ObjectId(test_id_loc)
        )
        agnostic = testobj.course_agnostic()
        self.check_block_locn_fields(
            agnostic,
            block='lab2',
            org=None,
            course=None,
            run=None,
            version_guid=ObjectId(test_id_loc)
        )
        self.assertIsNone(agnostic.course)
        self.assertIsNone(agnostic.run)
        self.assertIsNone(agnostic.org)

    def test_block_constructor_url_kitchen_sink(self):
        test_id_loc = '519665f6223ebd6980884f2b'
        testobj = UsageKey.from_string(
            f'block-v1:mit.eecs+6002x+2014_T2+{CourseLocator.BRANCH_PREFIX}'
            f'@draft+{CourseLocator.VERSION_PREFIX}@{test_id_loc}+'
            f'{BlockUsageLocator.BLOCK_TYPE_PREFIX}@problem+'
            f'{BlockUsageLocator.BLOCK_PREFIX}@lab2'
        )
        self.check_block_locn_fields(
            testobj,
            org='mit.eecs',
            course='6002x',
            run='2014_T2',
            branch='draft',
            block='lab2',
            version_guid=ObjectId(test_id_loc)
        )

    @ddt.data(*itertools.product(
        (
            f'{BLOCK_URL}{{}}',
        ),
        ('\n', '\n\n', ' ', '   ', '   \n'),
    ))
    @ddt.unpack
    def test_block_constructor_url_trailing_whitespace(self, url_fmt, whitespace):
        with self.assertRaises(InvalidKeyError):
            UsageKey.from_string(url_fmt.format(whitespace))

    def test_colon_name(self):
        """
        It seems we used to use colons in names; so, ensure they're acceptable.
        """
        org = 'mit.eecs'
        course = 'foo'
        run = '2014_T2'
        branch = 'foo'
        block_id = 'problem:with-colon~2'
        testobj = BlockUsageLocator(
            CourseLocator(org=org, course=course, run=run, branch=branch),
            block_type='problem',
            block_id=block_id
        )
        self.check_block_locn_fields(
            testobj, org=org, course=course, run=run, branch=branch, block=block_id
        )

    def test_relative(self):
        """
        Test making a relative usage locator.
        """
        org = 'mit.eecs'
        course = 'ponypower'
        run = "2014_T2"
        branch = 'foo'
        baseobj = CourseLocator(org=org, course=course, run=run, branch=branch)
        block_id = 'problem:with-colon~2'
        testobj = BlockUsageLocator.make_relative(baseobj, 'problem', block_id)
        self.check_block_locn_fields(
            testobj, org=org, course=course, run=run, branch=branch, block=block_id
        )
        block_id = 'completely_different'
        testobj = BlockUsageLocator.make_relative(testobj, 'problem', block_id)
        self.check_block_locn_fields(
            testobj, org=org, course=course, run=run, branch=branch, block=block_id
        )

    def test_repr(self):
        testurn = (
            f'block-v1:mit.eecs+6002x+2014_T2+{CourseLocator.BRANCH_PREFIX}'
            f'@published+{BlockUsageLocator.BLOCK_TYPE_PREFIX}'
            f'@problem+{BlockUsageLocator.BLOCK_PREFIX}@HW3'
        )
        testobj = UsageKey.from_string(testurn)
        expected = (
            f"BlockUsageLocator(CourseLocator({'mit.eecs'!r}, {'6002x'!r}, "
            f"{'2014_T2'!r}, {'published'!r}, None), {'problem'!r}, {'HW3'!r})"
        )
        self.assertEqual(expected, str(repr(testobj)))

    def test_local_id(self):
        local_id = LocalId()
        self.assertEqual(
            BlockUsageLocator(
                CourseLocator('org', 'course', 'run'),
                'problem',
                local_id
            ).block_id,
            local_id
        )
