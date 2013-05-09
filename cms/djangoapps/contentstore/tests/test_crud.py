'''
Created on May 7, 2013

@author: dmitchell
'''
import unittest
from xmodule import templates
from xmodule.modulestore.tests import factories
from xmodule.course_module import CourseDescriptor
from xmodule.modulestore.django import modulestore
from xmodule.seq_module import SequenceDescriptor
from xmodule.x_module import XModuleDescriptor
from xmodule.capa_module import CapaDescriptor


class TemplateTests(unittest.TestCase):
    """
    Test finding and using the templates (boilerplates) for xblocks.
    """

    def test_get_templates(self):
        found = templates.all_templates()
        self.assertIsNotNone(found.get('course'))
        self.assertIsNotNone(found.get('about'))
        self.assertIsNotNone(found.get('html'))
        self.assertIsNotNone(found.get('problem'))
        self.assertEqual(len(found.get('course')), 0)
        self.assertEqual(len(found.get('about')), 0)
        self.assertGreaterEqual(len(found.get('html')), 2)
        self.assertGreaterEqual(len(found.get('problem')), 10)
        dropdown = None
        for template in found['problem']:
            self.assertIn('display_name', template)
            if template['display_name'] == 'Dropdown':
                dropdown = template
                break
        self.assertIsNotNone(dropdown)
        self.assertIn('markdown', dropdown)
        self.assertIn('data', dropdown)
        self.assertRegexpMatches(dropdown['markdown'], r'^Dropdown.*')
        self.assertRegexpMatches(dropdown['data'], r'<problem>\s*<p>Dropdown.*')

    def test_factories(self):
        test_course = factories.CourseFactory.create(org='testx', prettyid='tempcourse',
            display_name='fun test course', user_id='testbot')
        self.assertIsInstance(test_course, CourseDescriptor)
        self.assertEqual(test_course.display_name, 'fun test course')
        index_info = modulestore().get_course_index_info(test_course.location)
        self.assertEqual(index_info['org'], 'testx')
        self.assertEqual(index_info['prettyid'], 'tempcourse')

        test_chapter = factories.ItemFactory.create(display_name='chapter 1',
            parent_location=test_course.location)
        self.assertIsInstance(test_chapter, SequenceDescriptor)
        # refetch parent which should now point to child
        test_course = modulestore().get_course(test_chapter.location)
        self.assertIn(test_chapter.location.usage_id, test_course.children)

    def test_temporary_xblocks(self):
        """
        Test using load_from_json to create non persisted xblocks
        """
        test_course = factories.CourseFactory.create(org='testx', prettyid='tempcourse',
            display_name='fun test course', user_id='testbot')

        test_chapter = XModuleDescriptor.load_from_json({'category': 'chapter',
            'metadata': {'display_name': 'chapter n'}},
            test_course.system, parent_xblock=test_course)
        self.assertIsInstance(test_chapter, SequenceDescriptor)
        self.assertEqual(test_chapter.display_name, 'chapter n')
        self.assertIn(test_chapter, test_course.get_children())

        # test w/ a definition (e.g., a problem)
        test_def_content = '<problem>boo</problem>'
        test_problem = XModuleDescriptor.load_from_json({'category': 'problem',
            'definition': {'data': test_def_content}},
            test_course.system, parent_xblock=test_chapter)
        self.assertIsInstance(test_problem, CapaDescriptor)
        self.assertEqual(test_problem.data, test_def_content)
        self.assertIn(test_problem, test_chapter.get_children())
        test_problem.display_name = 'test problem'
        self.assertEqual(test_problem.display_name, 'test problem')

    def test_persist_dag(self):
        """
        try saving temporary xblocks
        """
        test_course = factories.CourseFactory.create(org='testx', prettyid='tempcourse',
            display_name='fun test course', user_id='testbot')
        test_chapter = XModuleDescriptor.load_from_json({'category': 'chapter',
            'metadata': {'display_name': 'chapter n'}},
            test_course.system, parent_xblock=test_course)
        test_def_content = '<problem>boo</problem>'
        test_problem = XModuleDescriptor.load_from_json({'category': 'problem',
            'definition': {'data': test_def_content}},
            test_course.system, parent_xblock=test_chapter)
        # better to pass in persisted parent over the subdag so
        # subdag gets the parent pointer (otherwise 2 ops, persist dag, update parent children,
        # persist parent
        persisted_course = modulestore().persist_xblock_dag(test_course, 'testbot')
        self.assertEqual(len(persisted_course.children), 1)
        persisted_chapter = persisted_course.get_children()[0]
        self.assertEqual(persisted_chapter.category, 'chapter')
        self.assertEqual(persisted_chapter.display_name, 'chapter n')
        self.assertEqual(len(persisted_chapter.children), 1)
        persisted_problem = persisted_chapter.get_children()[0]
        self.assertEqual(persisted_problem.category, 'problem')
        self.assertEqual(persisted_problem.data, test_def_content)
