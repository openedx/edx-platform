import unittest

from xmodule import templates
from xmodule.modulestore.tests import persistent_factories
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore, loc_mapper, clear_existing_modulestores
from xmodule.seq_module import SequenceDescriptor
from xmodule.capa_module import CapaDescriptor
from xmodule.modulestore.locator import BlockUsageLocator, LocalId
from xmodule.modulestore.exceptions import ItemNotFoundError, DuplicateCourseError
from xmodule.html_module import HtmlDescriptor
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase


@unittest.skip("Not fixing split until we land opaque-keys 0.9")
class TemplateTests(unittest.TestCase):
    """
    Test finding and using the templates (boilerplates) for xblocks.
    """

    def setUp(self):
        clear_existing_modulestores()  # redundant w/ cleanup but someone was getting errors
        self.addCleanup(ModuleStoreTestCase.drop_mongo_collections, 'split')
        self.addCleanup(clear_existing_modulestores)

    def test_get_templates(self):
        found = templates.all_templates()
        self.assertIsNotNone(found.get('course'))
        self.assertIsNotNone(found.get('about'))
        self.assertIsNotNone(found.get('html'))
        self.assertIsNotNone(found.get('problem'))
        self.assertEqual(len(found.get('course')), 0)
        self.assertEqual(len(found.get('about')), 1)
        self.assertGreaterEqual(len(found.get('html')), 2)
        self.assertGreaterEqual(len(found.get('problem')), 10)
        dropdown = None
        for template in found['problem']:
            self.assertIn('metadata', template)
            self.assertIn('display_name', template['metadata'])
            if template['metadata']['display_name'] == 'Dropdown':
                dropdown = template
                break
        self.assertIsNotNone(dropdown)
        self.assertIn('markdown', dropdown['metadata'])
        self.assertIn('data', dropdown)
        self.assertRegexpMatches(dropdown['metadata']['markdown'], r'^Dropdown.*')
        self.assertRegexpMatches(dropdown['data'], r'<problem>\s*<p>Dropdown.*')

    def test_get_some_templates(self):
        self.assertEqual(len(SequenceDescriptor.templates()), 0)
        self.assertGreater(len(HtmlDescriptor.templates()), 0)
        self.assertIsNone(SequenceDescriptor.get_template('doesntexist.yaml'))
        self.assertIsNone(HtmlDescriptor.get_template('doesntexist.yaml'))
        self.assertIsNotNone(HtmlDescriptor.get_template('announcement.yaml'))

    def test_factories(self):
        test_course = persistent_factories.PersistentCourseFactory.create(
            course_id='testx.tempcourse', org='testx',
            display_name='fun test course', user_id='testbot'
        )
        self.assertIsInstance(test_course, CourseDescriptor)
        self.assertEqual(test_course.display_name, 'fun test course')
        index_info = modulestore('split').get_course_index_info(test_course.location)
        self.assertEqual(index_info['org'], 'testx')
        self.assertEqual(index_info['_id'], 'testx.tempcourse')

        test_chapter = persistent_factories.ItemFactory.create(display_name='chapter 1',
            parent_location=test_course.location)
        self.assertIsInstance(test_chapter, SequenceDescriptor)
        # refetch parent which should now point to child
        test_course = modulestore('split').get_course(test_course.id)
        self.assertIn(test_chapter.location.block_id, test_course.children)

        with self.assertRaises(DuplicateCourseError):
            persistent_factories.PersistentCourseFactory.create(
                course_id='testx.tempcourse', org='testx', 
                display_name='fun test course', user_id='testbot'
            )

    def test_temporary_xblocks(self):
        """
        Test create_xblock to create non persisted xblocks
        """
        test_course = persistent_factories.PersistentCourseFactory.create(
            course_id='testx.tempcourse', org='testx',
            display_name='fun test course', user_id='testbot'
        )

        test_chapter = modulestore('split').create_xblock(
            test_course.system, 'chapter', {'display_name': 'chapter n'}, parent_xblock=test_course
        )
        self.assertIsInstance(test_chapter, SequenceDescriptor)
        self.assertEqual(test_chapter.display_name, 'chapter n')
        self.assertIn(test_chapter, test_course.get_children())

        # test w/ a definition (e.g., a problem)
        test_def_content = '<problem>boo</problem>'
        test_problem = modulestore('split').create_xblock(
            test_course.system, 'problem', {'data': test_def_content}, parent_xblock=test_chapter
        )
        self.assertIsInstance(test_problem, CapaDescriptor)
        self.assertEqual(test_problem.data, test_def_content)
        self.assertIn(test_problem, test_chapter.get_children())
        test_problem.display_name = 'test problem'
        self.assertEqual(test_problem.display_name, 'test problem')

    def test_persist_dag(self):
        """
        try saving temporary xblocks
        """
        test_course = persistent_factories.PersistentCourseFactory.create(
            course_id='testx.tempcourse', org='testx', 
            display_name='fun test course', user_id='testbot'
        )
        test_chapter = modulestore('split').create_xblock(
            test_course.system, 'chapter', {'display_name': 'chapter n'}, parent_xblock=test_course
        )
        self.assertEqual(test_chapter.display_name, 'chapter n')
        test_def_content = '<problem>boo</problem>'
        # create child
        new_block = modulestore('split').create_xblock(
            test_course.system,
            'problem',
            fields={
                'data': test_def_content,
                'display_name': 'problem'
            },
            parent_xblock=test_chapter
        )
        self.assertIsNotNone(new_block.definition_locator)
        self.assertTrue(isinstance(new_block.definition_locator.definition_id, LocalId))
        # better to pass in persisted parent over the subdag so
        # subdag gets the parent pointer (otherwise 2 ops, persist dag, update parent children,
        # persist parent
        persisted_course = modulestore('split').persist_xblock_dag(test_course, 'testbot')
        self.assertEqual(len(persisted_course.children), 1)
        persisted_chapter = persisted_course.get_children()[0]
        self.assertEqual(persisted_chapter.category, 'chapter')
        self.assertEqual(persisted_chapter.display_name, 'chapter n')
        self.assertEqual(len(persisted_chapter.children), 1)
        persisted_problem = persisted_chapter.get_children()[0]
        self.assertEqual(persisted_problem.category, 'problem')
        self.assertEqual(persisted_problem.data, test_def_content)
        # update it
        persisted_problem.display_name = 'altered problem'
        persisted_problem = modulestore('split').persist_xblock_dag(persisted_problem, 'testbot')
        self.assertEqual(persisted_problem.display_name, 'altered problem')

    def test_delete_course(self):
        test_course = persistent_factories.PersistentCourseFactory.create(
            course_id='edu.harvard.history.doomed', org='testx',
            display_name='doomed test course',
            user_id='testbot')
        persistent_factories.ItemFactory.create(display_name='chapter 1',
            parent_location=test_course.location)

        id_locator = test_course.id.for_branch('draft')
        guid_locator = test_course.location.course_agnostic()
        # verify it can be retrieved by id
        self.assertIsInstance(modulestore('split').get_course(id_locator), CourseDescriptor)
        # and by guid
        self.assertIsInstance(modulestore('split').get_item(guid_locator), CourseDescriptor)
        modulestore('split').delete_course(id_locator)
        # test can no longer retrieve by id
        self.assertRaises(ItemNotFoundError, modulestore('split').get_course, id_locator)
        # but can by guid
        self.assertIsInstance(modulestore('split').get_item(guid_locator), CourseDescriptor)

    def test_block_generations(self):
        """
        Test get_block_generations
        """
        test_course = persistent_factories.PersistentCourseFactory.create(
            course_id='edu.harvard.history.hist101', org='testx',
            display_name='history test course',
            user_id='testbot'
        )
        chapter = persistent_factories.ItemFactory.create(display_name='chapter 1',
            parent_location=test_course.location, user_id='testbot')
        sub = persistent_factories.ItemFactory.create(display_name='subsection 1',
            parent_location=chapter.location, user_id='testbot', category='vertical')
        first_problem = persistent_factories.ItemFactory.create(
            display_name='problem 1', parent_location=sub.location, user_id='testbot', category='problem',
            data="<problem></problem>"
        )
        first_problem.max_attempts = 3
        first_problem.save()  # decache the above into the kvs
        updated_problem = modulestore('split').update_item(first_problem, '**replace_user**')
        self.assertIsNotNone(updated_problem.previous_version)
        self.assertEqual(updated_problem.previous_version, first_problem.update_version)
        self.assertNotEqual(updated_problem.update_version, first_problem.update_version)
        updated_loc = modulestore('split').delete_item(updated_problem.location, 'testbot', delete_children=True)

        second_problem = persistent_factories.ItemFactory.create(
            display_name='problem 2',
            parent_location=BlockUsageLocator.make_relative(updated_loc, block_id=sub.location.block_id),
            user_id='testbot', category='problem',
            data="<problem></problem>"
        )

        # course root only updated 2x
        version_history = modulestore('split').get_block_generations(test_course.location)
        self.assertEqual(version_history.locator.version_guid, test_course.location.version_guid)
        self.assertEqual(len(version_history.children), 1)
        self.assertEqual(version_history.children[0].children, [])
        self.assertEqual(version_history.children[0].locator.version_guid, chapter.location.version_guid)

        # sub changed on add, add problem, delete problem, add problem in strict linear seq
        version_history = modulestore('split').get_block_generations(sub.location)
        self.assertEqual(len(version_history.children), 1)
        self.assertEqual(len(version_history.children[0].children), 1)
        self.assertEqual(len(version_history.children[0].children[0].children), 1)
        self.assertEqual(len(version_history.children[0].children[0].children[0].children), 0)

        # first and second problem may show as same usage_id; so, need to ensure their histories are right
        version_history = modulestore('split').get_block_generations(updated_problem.location)
        self.assertEqual(version_history.locator.version_guid, first_problem.location.version_guid)
        self.assertEqual(len(version_history.children), 1)  # updated max_attempts
        self.assertEqual(len(version_history.children[0].children), 0)

        version_history = modulestore('split').get_block_generations(second_problem.location)
        self.assertNotEqual(version_history.locator.version_guid, first_problem.location.version_guid)

    def test_split_inject_loc_mapper(self):
        """
        Test that creating a loc_mapper causes it to automatically attach to the split mongo store
        """
        # instantiate location mapper before split
        mapper = loc_mapper()
        # split must inject the location mapper itself since the mapper existed before it did
        self.assertEqual(modulestore('split').loc_mapper, mapper)

    def test_loc_inject_into_split(self):
        """
        Test that creating a loc_mapper causes it to automatically attach to the split mongo store
        """
        # force instantiation of split modulestore before there's a location mapper and verify
        # it has no pointer to loc mapper
        self.assertIsNone(modulestore('split').loc_mapper)
        # force instantiation of location mapper which must inject itself into the split
        mapper = loc_mapper()
        self.assertEqual(modulestore('split').loc_mapper, mapper)

