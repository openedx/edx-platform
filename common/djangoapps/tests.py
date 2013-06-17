'''
Created on Jun 6, 2013

@author: dmitchell
'''
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from student.tests.factories import AdminFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
import xmodule_modifiers
import datetime
from pytz import UTC
from xmodule.modulestore.tests import factories

class TestXmoduleModfiers(ModuleStoreTestCase):

    # FIXME disabled b/c start date inheritance is not occuring and render_... in get_html is failing due
    # to middleware.lookup['main'] not being defined
    def _test_add_histogram(self):
        instructor = AdminFactory.create()
        self.client.login(username=instructor.username, password='test')

        course = CourseFactory.create(org='test',
            number='313', display_name='histogram test')
        section = ItemFactory.create(
            parent_location=course.location, display_name='chapter hist',
            template='i4x://edx/templates/chapter/Empty')
        problem = ItemFactory.create(
            parent_location=section.location, display_name='problem hist 1',
            template='i4x://edx/templates/problem/Blank_Common_Problem')
        problem.has_score = False  # don't trip trying to retrieve db data

        late_problem = ItemFactory.create(
            parent_location=section.location, display_name='problem hist 2',
            template='i4x://edx/templates/problem/Blank_Common_Problem')
        late_problem.lms.start = datetime.datetime.now(UTC) + datetime.timedelta(days=32)
        late_problem.has_score = False


        problem_module = factories.get_test_xmodule_for_descriptor(problem)
        problem_module.get_html = xmodule_modifiers.add_histogram(lambda:'', problem_module, instructor)

        self.assertRegexpMatches(
            problem_module.get_html(), r'.*<font color=\'green\'>Not yet</font>.*')

        problem_module = factories.get_test_xmodule_for_descriptor(late_problem)
        problem_module.get_html = xmodule_modifiers.add_histogram(lambda: '', problem_module, instructor)

        self.assertRegexpMatches(
            problem_module.get_html(), r'.*<font color=\'red\'>Yes!</font>.*')
