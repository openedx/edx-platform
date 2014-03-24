'''
Created on Aug 5, 2013

@author: dmitchell
'''
import unittest
import uuid
from xmodule.modulestore import Location
from xmodule.modulestore.locator import BlockUsageLocator
from xmodule.modulestore.exceptions import ItemNotFoundError, InvalidLocationError
from xmodule.modulestore.loc_mapper_store import LocMapperStore
from mock import Mock


class LocMapperSetupSansDjango(unittest.TestCase):
    """
    Create and destroy a loc mapper for each test
    """
    loc_store = None
    def setUp(self):
        modulestore_options = {
            'host': 'localhost',
            'db': 'test_xmodule',
            'collection': 'modulestore{0}'.format(uuid.uuid4().hex[:5]),
        }

        cache_standin = TrivialCache()
        self.instrumented_cache = Mock(spec=cache_standin, wraps=cache_standin)
        # pylint: disable=W0142
        LocMapperSetupSansDjango.loc_store = LocMapperStore(self.instrumented_cache, **modulestore_options)

    def tearDown(self):
        dbref = TestLocationMapper.loc_store.db
        dbref.drop_collection(TestLocationMapper.loc_store.location_map)
        dbref.connection.close()
        self.loc_store = None


class TestLocationMapper(LocMapperSetupSansDjango):
    """
    Test the location to locator mapper
    """
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

    def translate_n_check(self, location, old_style_course_id, new_style_package_id, block_id, branch, add_entry=False):
        """
        Request translation, check package_id, block_id, and branch
        """
        prob_locator = loc_mapper().translate_location(
            old_style_course_id,
            location,
            published= (branch=='published'),
            add_entry_if_missing=add_entry
        )
        self.assertEqual(prob_locator.package_id, new_style_package_id)
        self.assertEqual(prob_locator.block_id, block_id)
        self.assertEqual(prob_locator.branch, branch)

        course_locator = loc_mapper().translate_location_to_course_locator(
           old_style_course_id,
           location,
           published=(branch == 'published'),
        )
        self.assertEqual(course_locator.package_id, new_style_package_id)
        self.assertEqual(course_locator.branch, branch)

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

        new_style_package_id = '{}.geek_dept.{}.baz_run'.format(org, course)
        block_map = {
            'abc123': {'problem': 'problem2', 'vertical': 'vertical2'},
            'def456': {'problem': 'problem4'},
            'ghi789': {'problem': 'problem7'},
        }
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'course', 'baz_run'),
            new_style_package_id,
            block_map=block_map
        )
        test_problem_locn = Location('i4x', org, course, 'problem', 'abc123')
        # only one course matches

        # look for w/ only the Location (works b/c there's only one possible course match). Will force
        # cache as default translation for this problemid
        self.translate_n_check(test_problem_locn, None, new_style_package_id, 'problem2', 'published')
        # look for non-existent problem
        with self.assertRaises(ItemNotFoundError):
            loc_mapper().translate_location(
                None,
                Location('i4x', org, course, 'problem', '1def23'),
                add_entry_if_missing=False
            )
        test_no_cat_locn = test_problem_locn.replace(category=None)
        with self.assertRaises(InvalidLocationError):
            loc_mapper().translate_location(
                old_style_course_id, test_no_cat_locn, False, False
            )
        test_no_cat_locn = test_no_cat_locn.replace(name='def456')
        # only one course matches
        self.translate_n_check(test_no_cat_locn, old_style_course_id, new_style_package_id, 'problem4', 'published')

        # add a distractor course (note that abc123 has a different translation in this one)
        distractor_block_map = {
            'abc123': {'problem': 'problem3'},
            'def456': {'problem': 'problem4'},
            'ghi789': {'problem': 'problem7'},
        }
        test_delta_new_id = '{}.geek_dept.{}.{}'.format(org, course, 'delta_run')
        test_delta_old_id = '{}/{}/{}'.format(org, course, 'delta_run')
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'course', 'delta_run'),
            test_delta_new_id,
            block_map=distractor_block_map
        )
        # test that old translation still works
        self.translate_n_check(test_problem_locn, old_style_course_id, new_style_package_id, 'problem2', 'published')
        # and new returns new id
        self.translate_n_check(test_problem_locn, test_delta_old_id, test_delta_new_id, 'problem3', 'published')
        # look for default translation of uncached Location (not unique; so, just verify it returns something)
        prob_locator = loc_mapper().translate_location(
            None,
            Location('i4x', org, course, 'problem', 'def456'),
            add_entry_if_missing=False
        )
        self.assertIsNotNone(prob_locator, "couldn't find ambiguous location")

        # make delta_run default course: anything not cached using None as old_course_id will use this
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'problem', '789abc123efg456'),
            test_delta_new_id,
            block_map=block_map
        )
        # now an uncached ambiguous query should return delta
        test_unused_locn = Location('i4x', org, course, 'problem', 'ghi789')
        self.translate_n_check(test_unused_locn, None, test_delta_new_id, 'problem7', 'published')

        # get the draft one (I'm sorry this is getting long)
        self.translate_n_check(test_unused_locn, None, test_delta_new_id, 'problem7', 'draft')

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
        new_style_package_id = '{}.{}.{}'.format(org, course, 'baz_run')
        self.translate_n_check(location, old_style_course_id, new_style_package_id, 'problemabc', 'published', True)
        # look for w/ only the Location (works b/c there's only one possible course match): causes cache
        self.translate_n_check(location, None, new_style_package_id, 'problemabc', 'published', True)

        # create an entry w/o a guid name
        other_location = Location('i4x', org, course, 'chapter', 'intro')
        self.translate_n_check(other_location, old_style_course_id, new_style_package_id, 'intro', 'published', True)

        # add a distractor course
        delta_new_package_id = '{}.geek_dept.{}.{}'.format(org, course, 'delta_run')
        delta_course_locn = Location('i4x', org, course, 'course', 'delta_run')
        loc_mapper().create_map_entry(
            delta_course_locn,
            delta_new_package_id,
            block_map={problem_name: {'problem': 'problem3'}}
        )
        self.translate_n_check(location, old_style_course_id, new_style_package_id, 'problemabc', 'published', True)

        # add a new one to both courses (ensure name doesn't have same beginning)
        new_prob_name = uuid.uuid4().hex
        while new_prob_name.startswith('abc'):
            new_prob_name = uuid.uuid4().hex
        new_prob_locn = location.replace(name=new_prob_name)
        new_usage_id = 'problem{}'.format(new_prob_name[:3])
        self.translate_n_check(new_prob_locn, old_style_course_id, new_style_package_id, new_usage_id, 'published', True)
        self.translate_n_check(
            new_prob_locn, delta_course_locn.course_id, delta_new_package_id, new_usage_id, 'published', True
        )
        # look for w/ only the Location: causes caching and not unique; so, can't check which course
        prob_locator = loc_mapper().translate_location(
            None,
            new_prob_locn,
            add_entry_if_missing=True
        )
        self.assertIsNotNone(prob_locator, "couldn't find ambiguous location")

        # add a default course pointing to the delta_run
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'problem', '789abc123efg456'),
            delta_new_package_id,
            block_map={problem_name: {'problem': 'problem3'}}
        )
        # now the ambiguous query should return delta
        again_prob_name = uuid.uuid4().hex
        while again_prob_name.startswith('abc') or again_prob_name.startswith(new_prob_name[:3]):
            again_prob_name = uuid.uuid4().hex
        again_prob_locn = location.replace(name=again_prob_name)
        again_usage_id = 'problem{}'.format(again_prob_name[:3])
        self.translate_n_check(again_prob_locn, old_style_course_id, new_style_package_id, again_usage_id, 'published', True)
        self.translate_n_check(
            again_prob_locn, delta_course_locn.course_id, delta_new_package_id, again_usage_id, 'published', True
        )
        self.translate_n_check(again_prob_locn, None, delta_new_package_id, again_usage_id, 'published', True)

    def test_translate_locator(self):
        """
        tests translate_locator_to_location(BlockUsageLocator)
        """
        # lookup for non-existent course
        org = 'foo_org'
        course = 'bar_course'
        new_style_package_id = '{}.geek_dept.{}.baz_run'.format(org, course)
        prob_locator = BlockUsageLocator(
            package_id=new_style_package_id,
            block_id='problem2',
            branch='published'
        )
        prob_location = loc_mapper().translate_locator_to_location(prob_locator)
        self.assertIsNone(prob_location, 'found entry in empty map table')

        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'course', 'baz_run'),
            new_style_package_id,
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
            package_id=prob_locator.package_id, branch='draft', block_id=prob_locator.block_id
        )
        prob_location = loc_mapper().translate_locator_to_location(prob_locator)
        # Even though the problem was set as draft, we always return revision=None to work
        # with old mongo/draft modulestores.
        self.assertEqual(prob_location, Location('i4x', org, course, 'problem', 'abc123', None))
        prob_locator = BlockUsageLocator(
            package_id=new_style_package_id, block_id='problem2', branch='production'
        )
        prob_location = loc_mapper().translate_locator_to_location(prob_locator)
        self.assertEqual(prob_location, Location('i4x', org, course, 'problem', 'abc123', None))
        # same for chapter except chapter cannot be draft in old system
        chap_locator = BlockUsageLocator(
            package_id=new_style_package_id,
            block_id='chapter48f',
            branch='production'
        )
        chap_location = loc_mapper().translate_locator_to_location(chap_locator)
        self.assertEqual(chap_location, Location('i4x', org, course, 'chapter', '48f23a10395384929234'))
        # explicit branch
        chap_locator.branch = 'draft'
        chap_location = loc_mapper().translate_locator_to_location(chap_locator)
        self.assertEqual(chap_location, Location('i4x', org, course, 'chapter', '48f23a10395384929234'))
        chap_locator = BlockUsageLocator(
            package_id=new_style_package_id, block_id='chapter48f', branch='production'
        )
        chap_location = loc_mapper().translate_locator_to_location(chap_locator)
        self.assertEqual(chap_location, Location('i4x', org, course, 'chapter', '48f23a10395384929234'))

        # look for non-existent problem
        prob_locator2 = BlockUsageLocator(
            package_id=new_style_package_id,
            branch='draft',
            block_id='problem3'
        )
        prob_location = loc_mapper().translate_locator_to_location(prob_locator2)
        self.assertIsNone(prob_location, 'Found non-existent problem')

        # add a distractor course
        new_style_package_id = '{}.geek_dept.{}.{}'.format(org, course, 'delta_run')
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'course', 'delta_run'),
            new_style_package_id,
            block_map={'abc123': {'problem': 'problem3'}}
        )
        prob_location = loc_mapper().translate_locator_to_location(prob_locator)
        self.assertEqual(prob_location, Location('i4x', org, course, 'problem', 'abc123', None))

        # add a default course pointing to the delta_run
        loc_mapper().create_map_entry(
            Location('i4x', org, course, 'problem', '789abc123efg456'),
            new_style_package_id,
            block_map={'abc123': {'problem': 'problem3'}}
        )
        # now query delta (2 entries point to it)
        prob_locator = BlockUsageLocator(
            package_id=new_style_package_id,
            branch='production',
            block_id='problem3'
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

    def test_name_collision(self):
        """
        Test dwim translation when the old name was not unique
        """
        org = "myorg"
        course = "another_course"
        name = "running_again"
        course_location = Location('i4x', org, course, 'course', name)
        course_xlate = loc_mapper().translate_location(None, course_location, add_entry_if_missing=True)
        self.assertEqual(course_location, loc_mapper().translate_locator_to_location(course_xlate))
        eponymous_block = course_location.replace(category='chapter')
        chapter_xlate = loc_mapper().translate_location(None, eponymous_block, add_entry_if_missing=True)
        self.assertEqual(course_location, loc_mapper().translate_locator_to_location(course_xlate))
        self.assertEqual(eponymous_block, loc_mapper().translate_locator_to_location(chapter_xlate))
        # and a non-existent one w/o add
        eponymous_block = course_location.replace(category='problem')
        with self.assertRaises(ItemNotFoundError):
            chapter_xlate = loc_mapper().translate_location(None, eponymous_block, add_entry_if_missing=False)


#==================================
# functions to mock existing services
def loc_mapper():
    """
    Mocks the global location mapper.
    """
    return LocMapperSetupSansDjango.loc_store


def render_to_template_mock(*_args):
    """
    Mocks the mako render_to_template w/ a noop
    """


class TrivialCache(object):
    """
    A trivial cache impl
    """
    def __init__(self):
        self.cache = {}

    def get(self, key, default=None):
        """
        Mock the .get
        """
        return self.cache.get(key, default)

    def set_many(self, entries):
        """
        mock set_many
        """
        self.cache.update(entries)

    def set(self, key, entry):
        """
        mock set
        """
        self.cache[key] = entry
