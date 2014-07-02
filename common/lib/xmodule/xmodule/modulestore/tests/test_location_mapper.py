"""
Test the loc mapper store
"""
import unittest
import uuid
from opaque_keys.edx.locations import Location
from opaque_keys.edx.locator import BlockUsageLocator, CourseLocator
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.mongo.base import MongoRevisionKey
from xmodule.modulestore.exceptions import ItemNotFoundError, InvalidLocationError
from xmodule.modulestore.loc_mapper_store import LocMapperStore
from mock import Mock
from opaque_keys.edx.locations import SlashSeparatedCourseKey
import bson.son


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
    @unittest.skip("getting rid of loc_mapper")
    def test_create_map(self):
        def _construct_course_son(org, course, run):
            """
            Make a lookup son
            """
            return bson.son.SON([
                ('org', org),
                ('course', course),
                ('name', run)
            ])

        org = 'foo_org'
        course1 = 'bar_course'
        run = 'baz_run'
        loc_mapper().create_map_entry(SlashSeparatedCourseKey(org, course1, run))
        # pylint: disable=protected-access
        entry = loc_mapper().location_map.find_one({
            '_id': _construct_course_son(org, course1, run)
        })
        self.assertIsNotNone(entry, "Didn't find entry")
        self.assertEqual(entry['org'], org)
        self.assertEqual(entry['offering'], '{}.{}'.format(course1, run))
        self.assertEqual(entry['draft_branch'], ModuleStoreEnum.BranchName.draft)
        self.assertEqual(entry['prod_branch'], ModuleStoreEnum.BranchName.published)
        self.assertEqual(entry['block_map'], {})

        course2 = 'quux_course'
        # oldname: {category: newname}
        block_map = {'abc123': {'problem': 'problem2'}}
        loc_mapper().create_map_entry(
            SlashSeparatedCourseKey(org, course2, run),
            'foo_org.geek_dept',
            'quux_course.baz_run',
            'wip',
            'live',
            block_map)
        entry = loc_mapper().location_map.find_one({
            '_id': _construct_course_son(org, course2, run)
        })
        self.assertIsNotNone(entry, "Didn't find entry")
        self.assertEqual(entry['org'], 'foo_org.geek_dept')
        self.assertEqual(entry['offering'], '{}.{}'.format(course2, run))
        self.assertEqual(entry['draft_branch'], 'wip')
        self.assertEqual(entry['prod_branch'], 'live')
        self.assertEqual(entry['block_map'], block_map)

    @unittest.skip("getting rid of loc_mapper")
    def test_delete_course_map(self):
        """
        Test that course location is properly remove from loc_mapper and cache when course is deleted
        """
        org = u'foo_org'
        course = u'bar_course'
        run = u'baz_run'
        course_location = SlashSeparatedCourseKey(org, course, run)
        loc_mapper().create_map_entry(course_location)
        # pylint: disable=protected-access
        entry = loc_mapper().location_map.find_one({
            '_id': loc_mapper()._construct_course_son(course_location)
        })
        self.assertIsNotNone(entry, 'Entry not found in loc_mapper')
        self.assertEqual(entry['offering'], u'{1}.{2}'.format(org, course, run))

        # now delete course location from loc_mapper and cache and test that course location no longer
        # exists in loca_mapper and cache
        loc_mapper().delete_course_mapping(course_location)
        # pylint: disable=protected-access
        entry = loc_mapper().location_map.find_one({
            '_id': loc_mapper()._construct_course_son(course_location)
        })
        self.assertIsNone(entry, 'Entry found in loc_mapper')
        # pylint: disable=protected-access
        cached_value = loc_mapper()._get_location_from_cache(course_location.make_usage_key('course', run))
        self.assertIsNone(cached_value, 'course_locator found in cache')
        # pylint: disable=protected-access
        cached_value = loc_mapper()._get_course_location_from_cache(course_location)
        self.assertIsNone(cached_value, 'Entry found in cache')

    @unittest.skip("getting rid of loc_mapper")
    def translate_n_check(self, location, org, offering, block_id, branch, add_entry=False):
        """
        Request translation, check org, offering, block_id, and branch
        """
        prob_locator = loc_mapper().translate_location(
            location,
            published=(branch == ModuleStoreEnum.BranchName.published),
            add_entry_if_missing=add_entry
        )
        self.assertEqual(prob_locator.org, org)
        self.assertEqual(prob_locator.offering, offering)
        self.assertEqual(prob_locator.block_id, block_id)
        self.assertEqual(prob_locator.branch, branch)

        course_locator = loc_mapper().translate_location_to_course_locator(
            location.course_key,
            published=(branch == ModuleStoreEnum.BranchName.published),
        )
        self.assertEqual(course_locator.org, org)
        self.assertEqual(course_locator.offering, offering)
        self.assertEqual(course_locator.branch, branch)

    @unittest.skip("getting rid of loc_mapper")
    def test_translate_location_read_only(self):
        """
        Test the variants of translate_location which don't create entries, just decode
        """
        # lookup before there are any maps
        org = 'foo_org'
        course = 'bar_course'
        run = 'baz_run'
        slash_course_key = SlashSeparatedCourseKey(org, course, run)
        with self.assertRaises(ItemNotFoundError):
            _ = loc_mapper().translate_location(
                Location(org, course, run, 'problem', 'abc123'),
                add_entry_if_missing=False
            )

        new_style_org = '{}.geek_dept'.format(org)
        new_style_offering = '.{}.{}'.format(course, run)
        block_map = {
            'abc123': {'problem': 'problem2', 'vertical': 'vertical2'},
            'def456': {'problem': 'problem4'},
            'ghi789': {'problem': 'problem7'},
        }
        loc_mapper().create_map_entry(
            slash_course_key,
            new_style_org, new_style_offering,
            block_map=block_map
        )
        test_problem_locn = Location(org, course, run, 'problem', 'abc123')

        self.translate_n_check(test_problem_locn, new_style_org, new_style_offering, 'problem2',
                               ModuleStoreEnum.BranchName.published)
        # look for non-existent problem
        with self.assertRaises(ItemNotFoundError):
            loc_mapper().translate_location(
                Location(org, course, run, 'problem', '1def23'),
                add_entry_if_missing=False
            )
        test_no_cat_locn = test_problem_locn.replace(category=None)
        with self.assertRaises(InvalidLocationError):
            loc_mapper().translate_location(
                slash_course_key.make_usage_key(None, 'abc123'), test_no_cat_locn, False, False
            )
        test_no_cat_locn = test_no_cat_locn.replace(name='def456')

        self.translate_n_check(
            test_no_cat_locn, new_style_org, new_style_offering, 'problem4', ModuleStoreEnum.BranchName.published
        )

        # add a distractor course (note that abc123 has a different translation in this one)
        distractor_block_map = {
            'abc123': {'problem': 'problem3'},
            'def456': {'problem': 'problem4'},
            'ghi789': {'problem': 'problem7'},
        }
        run = 'delta_run'
        test_delta_new_org = '{}.geek_dept'.format(org)
        test_delta_new_offering = '{}.{}'.format(course, run)
        loc_mapper().create_map_entry(
            SlashSeparatedCourseKey(org, course, run),
            test_delta_new_org, test_delta_new_offering,
            block_map=distractor_block_map
        )
        # test that old translation still works
        self.translate_n_check(
            test_problem_locn, new_style_org, new_style_offering, 'problem2', ModuleStoreEnum.BranchName.published
        )
        # and new returns new id
        self.translate_n_check(
            test_problem_locn.replace(run=run), test_delta_new_org, test_delta_new_offering,
            'problem3', ModuleStoreEnum.BranchName.published
        )

    @unittest.skip("getting rid of loc_mapper")
    def test_translate_location_dwim(self):
        """
        Test the location translation mechanisms which try to do-what-i-mean by creating new
        entries for never seen queries.
        """
        org = 'foo_org'
        course = 'bar_course'
        run = 'baz_run'
        problem_name = 'abc123abc123abc123abc123abc123f9'
        location = Location(org, course, run, 'problem', problem_name)
        new_offering = '{}.{}'.format(course, run)
        self.translate_n_check(location, org, new_offering, 'problemabc', ModuleStoreEnum.BranchName.published, True)

        # create an entry w/o a guid name
        other_location = Location(org, course, run, 'chapter', 'intro')
        self.translate_n_check(other_location, org, new_offering, 'intro', ModuleStoreEnum.BranchName.published, True)

        # add a distractor course
        delta_new_org = '{}.geek_dept'.format(org)
        run = 'delta_run'
        delta_new_offering = '{}.{}'.format(course, run)
        delta_course_locn = SlashSeparatedCourseKey(org, course, run)
        loc_mapper().create_map_entry(
            delta_course_locn,
            delta_new_org, delta_new_offering,
            block_map={problem_name: {'problem': 'problem3'}}
        )
        self.translate_n_check(location, org, new_offering, 'problemabc', ModuleStoreEnum.BranchName.published, True)

        # add a new one to both courses (ensure name doesn't have same beginning)
        new_prob_name = uuid.uuid4().hex
        while new_prob_name.startswith('abc'):
            new_prob_name = uuid.uuid4().hex
        new_prob_locn = location.replace(name=new_prob_name)
        new_usage_id = 'problem{}'.format(new_prob_name[:3])
        self.translate_n_check(new_prob_locn, org, new_offering, new_usage_id, ModuleStoreEnum.BranchName.published, True)
        new_prob_locn = new_prob_locn.replace(run=run)
        self.translate_n_check(
            new_prob_locn, delta_new_org, delta_new_offering, new_usage_id, ModuleStoreEnum.BranchName.published, True
        )

    @unittest.skip("getting rid of loc_mapper")
    def test_translate_locator(self):
        """
        tests translate_locator_to_location(BlockUsageLocator)
        """
        # lookup for non-existent course
        org = 'foo_org'
        course = 'bar_course'
        run = 'baz_run'
        new_style_org = '{}.geek_dept'.format(org)
        new_style_offering = '{}.{}'.format(course, run)
        prob_course_key = CourseLocator(
            org=new_style_org, offering=new_style_offering,
            branch=ModuleStoreEnum.BranchName.published,
        )
        prob_locator = BlockUsageLocator(
            prob_course_key,
            block_type='problem',
            block_id='problem2',
        )
        prob_location = loc_mapper().translate_locator_to_location(prob_locator)
        self.assertIsNone(prob_location, 'found entry in empty map table')

        loc_mapper().create_map_entry(
            SlashSeparatedCourseKey(org, course, run),
            new_style_org, new_style_offering,
            block_map={
                'abc123': {'problem': 'problem2'},
                '48f23a10395384929234': {'chapter': 'chapter48f'},
                'baz_run': {'course': 'root'},
            }
        )
        # only one course matches
        prob_location = loc_mapper().translate_locator_to_location(prob_locator)
        # default branch
        self.assertEqual(prob_location, Location(org, course, run, 'problem', 'abc123', MongoRevisionKey.published))
        # test get_course keyword
        prob_location = loc_mapper().translate_locator_to_location(prob_locator, get_course=True)
        self.assertEqual(prob_location, SlashSeparatedCourseKey(org, course, run))
        # explicit branch
        prob_locator = prob_locator.for_branch(ModuleStoreEnum.BranchName.draft)
        prob_location = loc_mapper().translate_locator_to_location(prob_locator)
        # Even though the problem was set as draft, we always return revision= MongoRevisionKey.published to work
        # with old mongo/draft modulestores.
        self.assertEqual(prob_location, Location(org, course, run, 'problem', 'abc123', MongoRevisionKey.published))
        prob_locator = BlockUsageLocator(
            prob_course_key.for_branch('production'),
            block_type='problem', block_id='problem2'
        )
        prob_location = loc_mapper().translate_locator_to_location(prob_locator)
        self.assertEqual(prob_location, Location(org, course, run, 'problem', 'abc123', MongoRevisionKey.published))
        # same for chapter except chapter cannot be draft in old system
        chap_locator = BlockUsageLocator(
            prob_course_key.for_branch('production'),
            block_type='chapter', block_id='chapter48f',
        )
        chap_location = loc_mapper().translate_locator_to_location(chap_locator)
        self.assertEqual(chap_location, Location(org, course, run, 'chapter', '48f23a10395384929234'))
        # explicit branch
        chap_locator = chap_locator.for_branch(ModuleStoreEnum.BranchName.draft)
        chap_location = loc_mapper().translate_locator_to_location(chap_locator)
        self.assertEqual(chap_location, Location(org, course, run, 'chapter', '48f23a10395384929234'))
        chap_locator = BlockUsageLocator(
            prob_course_key.for_branch('production'), block_type='chapter', block_id='chapter48f'
        )
        chap_location = loc_mapper().translate_locator_to_location(chap_locator)
        self.assertEqual(chap_location, Location(org, course, run, 'chapter', '48f23a10395384929234'))

        # look for non-existent problem
        prob_locator2 = BlockUsageLocator(
            prob_course_key.for_branch(ModuleStoreEnum.BranchName.draft),
            block_type='problem', block_id='problem3'
        )
        prob_location = loc_mapper().translate_locator_to_location(prob_locator2)
        self.assertIsNone(prob_location, 'Found non-existent problem')

        # add a distractor course
        delta_run = 'delta_run'
        new_style_offering = '{}.{}'.format(course, delta_run)
        loc_mapper().create_map_entry(
            SlashSeparatedCourseKey(org, course, delta_run),
            new_style_org, new_style_offering,
            block_map={'abc123': {'problem': 'problem3'}}
        )
        prob_location = loc_mapper().translate_locator_to_location(prob_locator)
        self.assertEqual(prob_location, Location(org, course, run, 'problem', 'abc123', MongoRevisionKey.published))

    @unittest.skip("getting rid of loc_mapper")
    def test_special_chars(self):
        """
        Test locations which have special characters
        """
        # afaik, location.check_list prevents $ in all fields
        org = 'foo.org.edu'
        course = 'bar.course-4'
        name = 'baz.run_4-3'
        location = Location(org, course, name, 'course', name)
        prob_locator = loc_mapper().translate_location(
            location,
            add_entry_if_missing=True
        )
        reverted_location = loc_mapper().translate_locator_to_location(prob_locator)
        self.assertEqual(location, reverted_location)

    @unittest.skip("getting rid of loc_mapper")
    def test_name_collision(self):
        """
        Test dwim translation when the old name was not unique
        """
        org = "myorg"
        course = "another_course"
        name = "running_again"
        course_location = Location(org, course, name, 'course', name)
        course_xlate = loc_mapper().translate_location(course_location, add_entry_if_missing=True)
        self.assertEqual(course_location, loc_mapper().translate_locator_to_location(course_xlate))
        eponymous_block = course_location.replace(category='chapter')
        chapter_xlate = loc_mapper().translate_location(eponymous_block, add_entry_if_missing=True)
        self.assertEqual(course_location, loc_mapper().translate_locator_to_location(course_xlate))
        self.assertEqual(eponymous_block, loc_mapper().translate_locator_to_location(chapter_xlate))
        # and a non-existent one w/o add
        eponymous_block = course_location.replace(category='problem')
        with self.assertRaises(ItemNotFoundError):
            chapter_xlate = loc_mapper().translate_location(eponymous_block, add_entry_if_missing=False)


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

    def delete_many(self, entries):
        """
        mock delete_many
        """
        for entry in entries:
            del self.cache[entry]
