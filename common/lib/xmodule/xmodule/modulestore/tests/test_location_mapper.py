'''
Created on Aug 5, 2013

@author: dmitchell
'''
import unittest
import uuid
from xmodule.modulestore import Location
from xmodule.modulestore.locator import BlockUsageLocator
from xmodule.modulestore.exceptions import ItemNotFoundError, DuplicateItemError
from xmodule.modulestore.loc_mapper_store import LocMapperStore


class TestLocationMapper(unittest.TestCase):
    """
    Test the location to locator mapper
    """

    def setUp(self):
        modulestore_options = {
            'host': 'localhost',
            'db': 'test_xmodule',
            'collection': 'modulestore{0}'.format(uuid.uuid4().hex),
        }

        # pylint: disable=W0142
        TestLocationMapper.loc_store = LocMapperStore(**modulestore_options)

    def tearDown(self):
        dbref = TestLocationMapper.loc_store.db
        dbref.drop_collection(TestLocationMapper.loc_store.location_map)
        dbref.connection.close()
        TestLocationMapper.loc_store = None

    def test_create_map(self):
        org = 'foo_org'
        course = 'bar_course'
        loc_mapper().create_map_entry(Location('i4x', org, course, 'course', 'baz_run'))
        # pylint: disable=protected-access
        entry = loc_mapper().location_map.find_one({
            '_id': loc_mapper()._construct_location_son(org, course, 'baz_run')
        })
        self.assertIsNotNone(entry, "Didn't find entry")
        self.assertEqual(entry['course_id'], '{}.{}.baz_run'.format(org, course))
        self.assertEqual(entry['draft_branch'], 'draft')
        self.assertEqual(entry['prod_branch'], 'published')
        self.assertEqual(entry['block_map'], {})

        # ensure create_entry does the right thing when not given a course (creates org/course
        # rather than org/course/run course_id)
        loc_mapper().create_map_entry(Location('i4x', org, course, 'vertical', 'baz_vert'))
        # find the one which has no name
        entry = loc_mapper().location_map.find_one({
            '_id' : loc_mapper()._construct_location_son(org, course, None)
        })
        self.assertIsNotNone(entry, "Didn't find entry")
        self.assertEqual(entry['course_id'], '{}.{}'.format(org, course))

        course = 'quux_course'
        # oldname: {category: newname}
        block_map = {'abc123': {'problem': 'problem2'}}
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'problem', 'abc123', 'draft'),
            'foo_org.geek_dept.quux_course.baz_run',
            'wip',
            'live',
            block_map)
        entry = loc_mapper().location_map.find_one({'_id.org': org, '_id.course': course})
        self.assertIsNotNone(entry, "Didn't find entry")
        self.assertEqual(entry['course_id'], 'foo_org.geek_dept.quux_course.baz_run')
        self.assertEqual(entry['draft_branch'], 'wip')
        self.assertEqual(entry['prod_branch'], 'live')
        self.assertEqual(entry['block_map'], block_map)

    def test_translate_location_read_only(self):
        """
        Test the variants of translate_location which don't create entries, just decode
        """
        # lookup before there are any maps
        org = 'foo_org'
        course = 'bar_course'
        old_style_course_id = '{}/{}/{}'.format(org, course, 'baz_run')
        with self.assertRaises(ItemNotFoundError):
            _ = loc_mapper().translate_location(
                old_style_course_id,
                Location('i4x', org, course, 'problem', 'abc123'),
                add_entry_if_missing=False
            )

        new_style_course_id = '{}.geek_dept.{}.baz_run'.format(org, course)
        block_map = {'abc123': {'problem': 'problem2'}}
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'course', 'baz_run'),
            new_style_course_id,
            block_map=block_map
        )
        # only one course matches
        prob_locator = loc_mapper().translate_location(
            old_style_course_id,
            Location('i4x', org, course, 'problem', 'abc123'),
            add_entry_if_missing=False
        )
        self.assertEqual(prob_locator.course_id, new_style_course_id)
        self.assertEqual(prob_locator.branch, 'published')
        self.assertEqual(prob_locator.usage_id, 'problem2')
        # look for w/ only the Location (works b/c there's only one possible course match)
        prob_locator = loc_mapper().translate_location(
            None,
            Location('i4x', org, course, 'problem', 'abc123'),
            add_entry_if_missing=False
        )
        self.assertEqual(prob_locator.course_id, new_style_course_id)
        # look for non-existent problem
        with self.assertRaises(ItemNotFoundError):
            prob_locator = loc_mapper().translate_location(
                None,
                Location('i4x', org, course, 'problem', '1def23'),
                add_entry_if_missing=False
            )

        # add a distractor course
        block_map = {'abc123': {'problem': 'problem3'}}
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'course', 'delta_run'),
            '{}.geek_dept.{}.{}'.format(org, course, 'delta_run'),
            block_map=block_map
        )
        prob_locator = loc_mapper().translate_location(
            old_style_course_id,
            Location('i4x', org, course, 'problem', 'abc123'),
            add_entry_if_missing=False
        )
        self.assertEqual(prob_locator.course_id, new_style_course_id)
        self.assertEqual(prob_locator.usage_id, 'problem2')
        # look for w/ only the Location (not unique; so, just verify it returns something)
        prob_locator = loc_mapper().translate_location(
            None,
            Location('i4x', org, course, 'problem', 'abc123'),
            add_entry_if_missing=False
        )
        self.assertIsNotNone(prob_locator, "couldn't find ambiguous location")

        # add a default course pointing to the delta_run
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'problem', '789abc123efg456'),
            '{}.geek_dept.{}.{}'.format(org, course, 'delta_run'),
            block_map=block_map
        )
        # now the ambiguous query should return delta
        prob_locator = loc_mapper().translate_location(
            None,
            Location('i4x', org, course, 'problem', 'abc123'),
            add_entry_if_missing=False
        )
        self.assertEqual(prob_locator.course_id, '{}.geek_dept.{}.{}'.format(org, course, 'delta_run'))
        self.assertEqual(prob_locator.usage_id, 'problem3')

        # get the draft one (I'm sorry this is getting long)
        prob_locator = loc_mapper().translate_location(
            None,
            Location('i4x', org, course, 'problem', 'abc123'),
            published=False,
            add_entry_if_missing=False
        )
        self.assertEqual(prob_locator.course_id, '{}.geek_dept.{}.{}'.format(org, course, 'delta_run'))
        self.assertEqual(prob_locator.usage_id, 'problem3')
        self.assertEqual(prob_locator.branch, 'draft')

    def test_translate_location_dwim(self):
        """
        Test the location translation mechanisms which try to do-what-i-mean by creating new
        entries for never seen queries.
        """
        org = 'foo_org'
        course = 'bar_course'
        old_style_course_id = '{}/{}/{}'.format(org, course, 'baz_run')
        problem_name = 'abc123abc123abc123abc123abc123f9'
        location = Location('i4x', org, course, 'problem', problem_name)
        prob_locator = loc_mapper().translate_location(
            old_style_course_id,
            location,
            add_entry_if_missing=True
        )
        new_style_course_id = '{}.{}.{}'.format(org, course, 'baz_run')
        self.assertEqual(prob_locator.course_id, new_style_course_id)
        self.assertEqual(prob_locator.branch, 'published')
        self.assertEqual(prob_locator.usage_id, 'problemabc')
        # look for w/ only the Location (works b/c there's only one possible course match)
        prob_locator = loc_mapper().translate_location(
            None,
            location,
            add_entry_if_missing=True
        )
        self.assertEqual(prob_locator.course_id, new_style_course_id)
        # create an entry w/o a guid name
        other_location = Location('i4x', org, course, 'chapter', 'intro')
        locator = loc_mapper().translate_location(
            old_style_course_id,
            other_location,
            add_entry_if_missing=True
        )
        self.assertEqual(locator.usage_id, 'intro')

        # add a distractor course
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'course', 'delta_run'),
            '{}.geek_dept.{}.{}'.format(org, course, 'delta_run'),
            block_map={problem_name: {'problem': 'problem3'}}
        )
        prob_locator = loc_mapper().translate_location(
            old_style_course_id,
            location,
            add_entry_if_missing=True
        )
        self.assertEqual(prob_locator.course_id, new_style_course_id)
        self.assertEqual(prob_locator.usage_id, 'problemabc')
        # look for w/ only the Location (not unique; so, just verify it returns something)
        prob_locator = loc_mapper().translate_location(
            None,
            location,
            add_entry_if_missing=True
        )
        self.assertIsNotNone(prob_locator, "couldn't find ambiguous location")

        # add a default course pointing to the delta_run
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'problem', '789abc123efg456'),
            '{}.geek_dept.{}.{}'.format(org, course, 'delta_run'),
            block_map={problem_name: {'problem': 'problem3'}}
        )
        # now the ambiguous query should return delta
        prob_locator = loc_mapper().translate_location(
            None,
            location,
            add_entry_if_missing=False
        )
        self.assertEqual(prob_locator.course_id, '{}.geek_dept.{}.{}'.format(org, course, 'delta_run'))
        self.assertEqual(prob_locator.usage_id, 'problem3')

    def test_translate_locator(self):
        """
        tests translate_locator_to_location(BlockUsageLocator)
        """
        # lookup for non-existent course
        org = 'foo_org'
        course = 'bar_course'
        new_style_course_id = '{}.geek_dept.{}.baz_run'.format(org, course)
        prob_locator = BlockUsageLocator(
            course_id=new_style_course_id,
            usage_id='problem2',
            branch='published'
        )
        prob_location = loc_mapper().translate_locator_to_location(prob_locator)
        self.assertIsNone(prob_location, 'found entry in empty map table')

        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'course', 'baz_run'),
            new_style_course_id,
            block_map={
                'abc123': {'problem': 'problem2'},
                '48f23a10395384929234': {'chapter': 'chapter48f'},
                'baz_run': {'course': 'root'},
            }
        )
        # only one course matches
        prob_location = loc_mapper().translate_locator_to_location(prob_locator)
        # default branch
        self.assertEqual(prob_location, Location('i4x', org, course, 'problem', 'abc123', None))
        # test get_course keyword
        prob_location = loc_mapper().translate_locator_to_location(prob_locator, get_course=True)
        self.assertEqual(prob_location, Location('i4x', org, course, 'course', 'baz_run', None))
        # explicit branch
        prob_locator = BlockUsageLocator(
            course_id=prob_locator.course_id, branch='draft', usage_id=prob_locator.usage_id
        )
        prob_location = loc_mapper().translate_locator_to_location(prob_locator)
        # Even though the problem was set as draft, we always return revision=None to work
        # with old mongo/draft modulestores.
        self.assertEqual(prob_location, Location('i4x', org, course, 'problem', 'abc123', None))
        prob_locator = BlockUsageLocator(
            course_id=new_style_course_id, usage_id='problem2', branch='production'
        )
        prob_location = loc_mapper().translate_locator_to_location(prob_locator)
        self.assertEqual(prob_location, Location('i4x', org, course, 'problem', 'abc123', None))
        # same for chapter except chapter cannot be draft in old system
        chap_locator = BlockUsageLocator(
            course_id=new_style_course_id,
            usage_id='chapter48f',
            branch='production'
        )
        chap_location = loc_mapper().translate_locator_to_location(chap_locator)
        self.assertEqual(chap_location, Location('i4x', org, course, 'chapter', '48f23a10395384929234'))
        # explicit branch
        chap_locator.branch = 'draft'
        chap_location = loc_mapper().translate_locator_to_location(chap_locator)
        self.assertEqual(chap_location, Location('i4x', org, course, 'chapter', '48f23a10395384929234'))
        chap_locator = BlockUsageLocator(
            course_id=new_style_course_id, usage_id='chapter48f', branch='production'
        )
        chap_location = loc_mapper().translate_locator_to_location(chap_locator)
        self.assertEqual(chap_location, Location('i4x', org, course, 'chapter', '48f23a10395384929234'))

        # look for non-existent problem
        prob_locator2 = BlockUsageLocator(
            course_id=new_style_course_id,
            branch='draft',
            usage_id='problem3'
        )
        prob_location = loc_mapper().translate_locator_to_location(prob_locator2)
        self.assertIsNone(prob_location, 'Found non-existent problem')

        # add a distractor course
        new_style_course_id = '{}.geek_dept.{}.{}'.format(org, course, 'delta_run')
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'course', 'delta_run'),
            new_style_course_id,
            block_map={'abc123': {'problem': 'problem3'}}
        )
        prob_location = loc_mapper().translate_locator_to_location(prob_locator)
        self.assertEqual(prob_location, Location('i4x', org, course, 'problem', 'abc123', None))

        # add a default course pointing to the delta_run
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'problem', '789abc123efg456'),
            new_style_course_id,
            block_map={'abc123': {'problem': 'problem3'}}
        )
        # now query delta (2 entries point to it)
        prob_locator = BlockUsageLocator(
            course_id=new_style_course_id,
            branch='production',
            usage_id='problem3'
        )
        prob_location = loc_mapper().translate_locator_to_location(prob_locator)
        self.assertEqual(prob_location, Location('i4x', org, course, 'problem', 'abc123'))

    def test_special_chars(self):
        """
        Test locations which have special characters
        """
        # afaik, location.check_list prevents $ in all fields
        org = 'foo.org.edu'
        course = 'bar.course-4'
        name = 'baz.run_4-3'
        old_style_course_id = '{}/{}/{}'.format(org, course, name)
        location = Location('i4x', org, course, 'course', name)
        prob_locator = loc_mapper().translate_location(
            old_style_course_id,
            location,
            add_entry_if_missing=True
        )
        reverted_location = loc_mapper().translate_locator_to_location(prob_locator)
        self.assertEqual(location, reverted_location)

    def test_add_block(self):
        """
        Test add_block_location_translator(location, old_course_id=None, usage_id=None)
        """
        # call w/ no matching courses
        org = 'foo_org'
        course = 'bar_course'
        old_style_course_id = '{}/{}/{}'.format(org, course, 'baz_run')
        problem_name = 'abc123abc123abc123abc123abc123f9'
        location = Location('i4x', org, course, 'problem', problem_name)
        with self.assertRaises(ItemNotFoundError):
            loc_mapper().add_block_location_translator(location)
        with self.assertRaises(ItemNotFoundError):
            loc_mapper().add_block_location_translator(location, old_style_course_id)

        # w/ one matching course
        new_style_course_id = '{}.{}.{}'.format(org, course, 'baz_run')
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'course', 'baz_run'),
            new_style_course_id,
        )
        new_usage_id = loc_mapper().add_block_location_translator(location)
        self.assertEqual(new_usage_id, 'problemabc')
        # look it up
        translated_loc = loc_mapper().translate_location(old_style_course_id, location, add_entry_if_missing=False)
        self.assertEqual(translated_loc.course_id, new_style_course_id)
        self.assertEqual(translated_loc.usage_id, new_usage_id)

        # w/ one distractor which has one entry already
        new_style_course_id = '{}.geek_dept.{}.{}'.format(org, course, 'delta_run')
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'course', 'delta_run'),
            new_style_course_id,
            block_map={'48f23a10395384929234': {'chapter': 'chapter48f'}}
        )
        # try adding the one added before
        new_usage_id2 = loc_mapper().add_block_location_translator(location)
        self.assertEqual(new_usage_id, new_usage_id2)
        # it should be in the distractor now
        new_location = loc_mapper().translate_locator_to_location(
            BlockUsageLocator(course_id=new_style_course_id, usage_id=new_usage_id2, branch='published')
        )
        self.assertEqual(new_location, location)
        # add one close to the existing chapter (cause name collision)
        location = Location('i4x', org, course, 'chapter', '48f23a103953849292341234567890ab')
        new_usage_id = loc_mapper().add_block_location_translator(location)
        self.assertRegexpMatches(new_usage_id, r'^chapter48f\d')
        # retrievable from both courses
        new_location = loc_mapper().translate_locator_to_location(
            BlockUsageLocator(course_id=new_style_course_id, usage_id=new_usage_id, branch='published')
        )
        self.assertEqual(new_location, location)
        new_location = loc_mapper().translate_locator_to_location(
            BlockUsageLocator(
                course_id='{}.{}.{}'.format(org, course, 'baz_run'),
                usage_id=new_usage_id,
                branch='published'
            )
        )
        self.assertEqual(new_location, location)

        # provoke duplicate item errors
        location = location.replace(name='44f23a103953849292341234567890ab')
        with self.assertRaises(DuplicateItemError):
            loc_mapper().add_block_location_translator(location, usage_id=new_usage_id)
        new_usage_id = loc_mapper().add_block_location_translator(location, old_course_id=old_style_course_id)
        other_course_old_style = '{}/{}/{}'.format(org, course, 'delta_run')
        new_usage_id2 = loc_mapper().add_block_location_translator(
            location,
            old_course_id=other_course_old_style,
            usage_id='{}b'.format(new_usage_id)
        )
        with self.assertRaises(DuplicateItemError):
            loc_mapper().add_block_location_translator(location)

    def test_update_block(self):
        """
        test update_block_location_translator(location, usage_id, old_course_id=None)
        """
        org = 'foo_org'
        course = 'bar_course'
        new_style_course_id = '{}.geek_dept.{}.baz_run'.format(org, course)
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'course', 'baz_run'),
            new_style_course_id,
            block_map={
                'abc123': {'problem': 'problem2'},
                '48f23a10395384929234': {'chapter': 'chapter48f'},
                '1': {'chapter': 'chapter1', 'problem': 'problem1'},
            }
        )
        new_style_course_id2 = '{}.geek_dept.{}.delta_run'.format(org, course)
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'course', 'delta_run'),
            new_style_course_id2,
            block_map={
                'abc123': {'problem': 'problem3'},
                '48f23a10395384929234': {'chapter': 'chapter48b'},
                '1': {'chapter': 'chapter2', 'problem': 'problem2'},
            }
        )
        location = Location('i4x', org, course, 'problem', '1')
        # change in all courses to same value
        loc_mapper().update_block_location_translator(location, 'problem1')
        trans_loc = loc_mapper().translate_locator_to_location(
            BlockUsageLocator(course_id=new_style_course_id, usage_id='problem1', branch='published')
        )
        self.assertEqual(trans_loc, location)
        trans_loc = loc_mapper().translate_locator_to_location(
            BlockUsageLocator(course_id=new_style_course_id2, usage_id='problem1', branch='published')
        )
        self.assertEqual(trans_loc, location)
        # try to change to overwrite used usage_id
        location = Location('i4x', org, course, 'chapter', '48f23a10395384929234')
        with self.assertRaises(DuplicateItemError):
            loc_mapper().update_block_location_translator(location, 'chapter2')
        # just change the one course
        loc_mapper().update_block_location_translator(location, 'chapter2', '{}/{}/{}'.format(org, course, 'baz_run'))
        trans_loc = loc_mapper().translate_locator_to_location(
            BlockUsageLocator(course_id=new_style_course_id, usage_id='chapter2', branch='published')
        )
        self.assertEqual(trans_loc.name, '48f23a10395384929234')
        # but this still points to the old
        trans_loc = loc_mapper().translate_locator_to_location(
            BlockUsageLocator(course_id=new_style_course_id2, usage_id='chapter2', branch='published')
        )
        self.assertEqual(trans_loc.name, '1')

    def test_delete_block(self):
        """
        test delete_block_location_translator(location, old_course_id=None)
        """
        org = 'foo_org'
        course = 'bar_course'
        new_style_course_id = '{}.geek_dept.{}.baz_run'.format(org, course)
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'course', 'baz_run'),
            new_style_course_id,
            block_map={
                'abc123': {'problem': 'problem2'},
                '48f23a10395384929234': {'chapter': 'chapter48f'},
                '1': {'chapter': 'chapter1', 'problem': 'problem1'},
            }
        )
        new_style_course_id2 = '{}.geek_dept.{}.delta_run'.format(org, course)
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'course', 'delta_run'),
            new_style_course_id2,
            block_map={
                'abc123': {'problem': 'problem3'},
                '48f23a10395384929234': {'chapter': 'chapter48b'},
                '1': {'chapter': 'chapter2', 'problem': 'problem2'},
            }
        )
        location = Location('i4x', org, course, 'problem', '1')
        # delete from all courses
        loc_mapper().delete_block_location_translator(location)
        self.assertIsNone(loc_mapper().translate_locator_to_location(
            BlockUsageLocator(course_id=new_style_course_id, usage_id='problem1', branch='published')
        ))
        self.assertIsNone(loc_mapper().translate_locator_to_location(
            BlockUsageLocator(course_id=new_style_course_id2, usage_id='problem2', branch='published')
        ))
        # delete from one course
        location = location.replace(name='abc123')
        loc_mapper().delete_block_location_translator(location, '{}/{}/{}'.format(org, course, 'baz_run'))
        with self.assertRaises(ItemNotFoundError):
            loc_mapper().translate_location(
                '{}/{}/{}'.format(org, course, 'baz_run'),
                location,
                add_entry_if_missing=False
            )
        locator = loc_mapper().translate_location(
            '{}/{}/{}'.format(org, course, 'delta_run'),
            location,
            add_entry_if_missing=False
        )
        self.assertEqual(locator.usage_id, 'problem3')


#==================================
# functions to mock existing services
def loc_mapper():
    """
    Mocks the global location mapper.
    """
    return TestLocationMapper.loc_store


def render_to_template_mock(*_args):
    """
    Mocks the mako render_to_template w/ a noop
    """
