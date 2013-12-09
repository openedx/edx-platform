import datetime
import json
import mock
import unittest


due_date = datetime.datetime(2010, 5, 12, 2, 42)
extended_due_date = datetime.datetime(2013, 10, 12, 10, 30)


class ExtensionsTests(unittest.TestCase):

    def setUp(self):
        self.course = DummyCourseNode(
            'Dummy Course', 'i4x://dummy',
            children = [
                DummyCourseNode(
                    'Homework 1', 'i4x://dummy/homework',
                    due=due_date,
                    children=[
                        DummyCourseNode(
                            'Problem 1', 'i4x://dummy/homework/problem')]),
                DummyCourseNode(
                    'Final Exam', 'i4x://dummy/exam',
                    due=due_date,
                    children=[
                        DummyCourseNode(
                            'Problem 2', 'i4x://dummy/exam/problem')])])
        self.homework, self.exam = self.course.children

        patcher = mock.patch('instructor.views.extensions.StudentModule')
        self.StudentModule = patcher.start()
        self.addCleanup(patcher.stop)

        self.student = mock.Mock(username='fred', first_name='Fred',
                                 last_name='Flintstone')

    def test_set_due_date_extension_success(self):
        from ..extensions import set_due_date_extension as fut
        self.StudentModule.objects.get.return_value.state = json.dumps({})
        error, unit = fut(self.course, 'i4x://dummy/homework', self.student,
                          extended_due_date)
        self.assertEqual(error, None)
        state = json.loads(self.StudentModule.objects.get.return_value.state)
        self.assertEqual(state['extended_due'], u'2013-10-12T10:30:00Z')

    def test_set_due_date_extension_bad_url(self):
        from ..extensions import set_due_date_extension as fut
        error, unit = fut(self.course, 'i4x://foo', self.student,
                          extended_due_date)
        self.assertTrue(error.startswith("Couldn't find"))

    def test_dump_students_with_due_date_extensions(self):
        from ..extensions import dump_students_with_due_date_extensions as fut
        class DummyProfile(object):
            def __init__(self, name):
                self.name = name
        self.StudentModule.objects.filter.return_value = [
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
        self.assertEqual(table['data'],
          [('barney', 'Barney Rubble', '2013-10-13 10:30'),
           ('fred', 'Fred Flintstone', '2013-10-12 10:30')])

    def test_dump_students_with_due_date_extensions_bad_url(self):
        from ..extensions import dump_students_with_due_date_extensions as fut
        error, table = fut(self.course, 'i4x://foo')
        self.assertTrue(error.startswith("Couldn't find"))
        self.assertEqual(table, {})

    def test_dump_due_date_extensions_for_student(self):
        from ..extensions import dump_due_date_extensions_for_student as fut
        self.StudentModule.objects.filter.return_value = [
            mock.Mock(
                module_state_key='i4x://dummy/homework',
                state=json.dumps({})),
            mock.Mock(
                module_state_key='i4x://dummy/exam',
                state=json.dumps({'extended_due': u'2013-10-13T10:30:00Z'}))]
        error, table = fut(self.course, self.student)
        self.assertEqual(error, None)
        self.assertEqual(table['header'], ["Unit", "Extended Due Date"])
        self.assertEqual(table['title'],
                         "Due date extensions for Fred Flintstone (fred)")
        self.assertEqual(table['data'],
                         [('Final Exam', '2013-10-13 10:30')])


class DummyCourseNode(object):
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

