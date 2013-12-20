"""
Test due date extensions library.
"""

import datetime
import json
import mock
import unittest


DUE_DATE = datetime.datetime(2010, 5, 12, 2, 42)
EXTENDED_DUE_DATE = datetime.datetime(2013, 10, 12, 10, 30)


class ExtensionsTests(unittest.TestCase):
    """
    Test due date extensions library.
    """

    def setUp(self):
        """
        Set up test fixtures.
        """
        self.course = DummyCourseNode(
            'Dummy Course', 'i4x://dummy',
            children=[
                DummyCourseNode(
                    'Homework 1', 'i4x://dummy/homework',
                    due=DUE_DATE,
                    children=[
                        DummyCourseNode(
                            'Problem 1', 'i4x://dummy/homework/problem')]),
                DummyCourseNode(
                    'Final Exam', 'i4x://dummy/exam',
                    due=DUE_DATE,
                    children=[
                        DummyCourseNode(
                            'Problem 2', 'i4x://dummy/exam/problem')])])
        self.homework, self.exam = self.course.children

        patcher = mock.patch('instructor.views.extensions.StudentModule')
        self.student_module = patcher.start()
        self.addCleanup(patcher.stop)

        self.student = mock.Mock(username='fred', first_name='Fred',
                                 last_name='Flintstone')

    def test_set_due_date_extension_success(self):
        """
        Test setting a due date extension.
        """
        from ..extensions import set_due_date_extension as fut
        self.student_module.objects.get.return_value.state = json.dumps({})
        error, _ = fut(self.course, 'i4x://dummy/homework', self.student,
                       EXTENDED_DUE_DATE)
        self.assertEqual(error, None)
        state = json.loads(self.student_module.objects.get.return_value.state)
        self.assertEqual(state['extended_due'], u'2013-10-12T10:30:00Z')

    def test_set_due_date_extension_bad_url(self):
        """
        Test attempt to set due date extension with bad url.
        """
        from ..extensions import set_due_date_extension as fut
        error, _ = fut(self.course, 'i4x://foo', self.student,
                       EXTENDED_DUE_DATE)
        self.assertTrue(error.startswith("Couldn't find"))

    def test_dump_module_extensions(self):
        """
        Test dump of students with due date extensions.
        """
        from ..extensions import dump_module_extensions as fut

        class DummyProfile(object):
            "Mock Profile"
            def __init__(self, name):
                self.name = name
        self.student_module.objects.filter.return_value = [
            mock.Mock(
                student=mock.Mock(
                    username='fred',
                    profile=DummyProfile('Fred Flintstone')),
                state=json.dumps({'extended_due': u'2013-10-12T10:30:00Z'})),
            mock.Mock(
                student=mock.Mock(
                    username='barney',
                    profile=DummyProfile('Barney Rubble')),
                state=json.dumps({'extended_due': u'2013-10-13T10:30:00Z'})),
            mock.Mock(
                student=mock.Mock(
                    username='bambam',
                    first_name='Bam Bam',
                    last_name='Flintstone'),
                state=json.dumps({}))]
        error, table = fut(self.course, 'i4x://dummy/homework')
        self.assertEqual(error, None)
        self.assertEqual(table['header'],
                         ["Username", "Full Name", "Extended Due Date"])
        self.assertEqual(table['title'],
                         "Users with due date extensions for Homework 1")
        self.assertEqual(
            table['data'],
            [('barney', 'Barney Rubble', '2013-10-13 10:30'),
             ('fred', 'Fred Flintstone', '2013-10-12 10:30')])

    def test_dump_module_extensions_bad_url(self):
        """
        Test attempt to dump students with due date extenions with bad url.
        """
        from ..extensions import dump_module_extensions as fut
        error, table = fut(self.course, 'i4x://foo')
        self.assertTrue(error.startswith("Couldn't find"))
        self.assertEqual(table, {})

    def test_dump_student_extensions(self):
        """
        Test dump due date extensions for student.
        """
        from ..extensions import dump_student_extensions as fut
        self.student_module.objects.filter.return_value = [
            mock.Mock(
                module_state_key='i4x://dummy/homework',
                state=json.dumps({})),
            mock.Mock(
                module_state_key='i4x://dummy/exam',
                state=json.dumps({'extended_due': u'2013-10-13T10:30:00Z'}))]
        table = fut(self.course, self.student)
        self.assertEqual(table['header'], ["Unit", "Extended Due Date"])
        self.assertEqual(table['title'],
                         "Due date extensions for Fred Flintstone (fred)")
        self.assertEqual(table['data'],
                         [('Final Exam', '2013-10-13 10:30')])


class DummyCourseNode(object):
    """
    Mock of a CourseNode.
    """
    id = 1
    children = []

    def __init__(self, display_name, url, **kw):
        self.display_name = display_name
        self._url = url
        self.__dict__.update(kw)

    @property
    def location(self):
        return self

    def url(self):
        return self._url

    def get_children(self):
        return self.children
