from django.test import TestCase
from mock import MagicMock, patch, ANY
from contextlib import nested
from pgreport.views import (
    ProgressReport, UserDoesNotExists, InvalidCommand,
    get_pgreport_csv, create_pgreport_csv, delete_pgreport_csv,
    get_pgreport_table, update_pgreport_table
)
from pgreport.models import ProgressModules, ProgressModulesHistory
from django.test.utils import override_settings
from courseware.tests.modulestore_config import TEST_DATA_MIXED_MODULESTORE
from opaque_keys.edx.locator import CourseLocator
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase

import factory
from factory.django import DjangoModelFactory
from student.tests.factories import UserFactory, UserStandingFactory, CourseEnrollmentFactory
from courseware.tests.factories import (InstructorFactory, StaffFactory)
from django.contrib.auth.models import User
from student.models import UserStanding
from gridfs.errors import GridFSError
from xmodule.exceptions import NotFoundError
from django.db import DatabaseError

from pytz import UTC
import datetime
import StringIO
import gzip


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class ProgressReportTestCase(ModuleStoreTestCase):
    """ Test Progress Report """
    COURSE_NAME = "test_pgreport"
    COURSE_NUM = 3

    def setUp(self):
        self.output = StringIO.StringIO()
        self.gzipfile = StringIO.StringIO()
        self.course = CourseFactory.create(
            display_name=self.COURSE_NAME,
        )
        self.course.raw_grader = [{
            'drop_count': 0,
            'min_count': 1,
            'short_label': 'Final',
            'type': 'Final Exam',
            'weight': 1.0
        }]
        self.course.grade_cutoffs = {'Pass': 0.1}
        self.students = [
            UserFactory.create(username='student1'),
            UserFactory.create(username='student2'),
            UserFactory.create(username='student3'),
            UserFactory.create(username='student4'),
            UserFactory.create(username='student5'),
            StaffFactory.create(username='staff1', course_key=self.course.id),
            InstructorFactory.create(username='instructor1', course_key=self.course.id),
        ]
        UserStandingFactory.create(
            user=self.students[4],
            account_status=UserStanding.ACCOUNT_DISABLED,
            changed_by=self.students[6]
        )

        for user in self.students:
            CourseEnrollmentFactory.create(user=user, course_id=self.course.id)

        self.pgreport = ProgressReport(self.course.id)
        self.pgreport2 = ProgressReport(self.course.id, lambda state: state)

        self.chapter = ItemFactory.create(
            parent_location=self.course.location,
            category="chapter",
            display_name="Week 1"
        )
        self.chapter.save()
        self.section = ItemFactory.create(
            parent_location=self.chapter.location,
            category="sequential",
            display_name="Lesson 1"
        )
        self.section.save()
        self.vertical = ItemFactory.create(
            parent_location=self.section.location,
            category="vertical",
            display_name="Unit1"
        )
        self.vertical.save()
        self.html = ItemFactory.create(
            parent_location=self.vertical.location,
            category="html",
            data={'data': "<html>foobar</html>"}
        )
        self.html.save()
        """
        course.children = [week1.location.url(), week2.location.url(),
                           week3.location.url()]
        """
        from capa.tests.response_xml_factory import OptionResponseXMLFactory
        self.problem_xml = OptionResponseXMLFactory().build_xml(
            question_text='The correct answer is Correct',
            num_inputs=2,
            weight=2,
            options=['Correct', 'Incorrect'],
            correct_option='Correct'
        )

        self.problems = []
        for num in xrange(1, 3):
            self.problems.append(ItemFactory.create(
                parent_location=self.vertical.location,
                category='problem',
                display_name='problem_' + str(num),
                metadata={'graded': True, 'format': 'Final Exam'},
                data=self.problem_xml
            ))
            self.problems[num - 1].save()

        for problem in self.problems:
            problem.correct_map = {
                unicode(problem.location) + "_2_1": {
                    "hint": "",
                    "hintmode": "",
                    "correctness": "correct",
                    "npoints": "",
                    "msg": "",
                    "queuestate": ""
                },
                unicode(problem.location) + "_2_2": {
                    "hint": "",
                    "hintmode": "",
                    "correctness": "incorrect",
                    "npoints": "",
                    "msg": "",
                    "queuestate": ""
                }
            }

            problem.student_answers = {
                unicode(problem.location) + "_2_1": "Correct",
                unicode(problem.location) + "_2_2": "Incorrect"
            }

            problem.input_state = {
                unicode(problem.location) + "_2_1": {},
                unicode(problem.location) + "_2_2": {}
            }

        self.course.save()

        patcher = patch('pgreport.views.logging')
        self.log_mock = patcher.start()
        self.addCleanup(patcher.stop)

        """
        from xmodule.modulestore import Location
        import json
        for user in self.students:
            StudentModuleFactory.create(
                grade=1,
                max_grade=1,
                student=user,
                course_id=self.course.id,
                #module_state_key=Location(self.problem).url(),
                module_state_key=self.problem.location.url(),
                #state = json.dumps({'attempts': self.attempts, 'done':True})
                state = json.dumps({'done':True})
            )

        ./lms/djangoapps/courseware/management/commands/tests/test_dump_course.py
        def load_courses(self):
        cp xmport-course common/test/data and modify TEST_DATA_MIXED_MODULESTORE
        """

    def tearDown(self):
        self.output.close()
        self.gzipfile.close()

    def test_get_active_students(self):
        counts, actives, users = ProgressReport.get_active_students(self.course.id)
        self.assertEquals(counts, 7)
        self.assertEquals(actives, 6)
        self.assertItemsEqual(users, self.students[:4] + self.students[5:])

        fake_course = CourseFactory.create(display_name="fake")
        with self.assertRaises(UserDoesNotExists):
            counts, actives, users = ProgressReport.get_active_students(fake_course.id)

    def test_create_request(self):
        from django.core.handlers.wsgi import WSGIRequest
        request = self.pgreport._create_request()
        self.assertIsInstance(request, WSGIRequest)

    def test_calc_statistics(self):
        self.pgreport.module_statistics = {
            self.problems[0].location: [1.0, 5.6, 3.4, 9.8, 20.2],
            self.problems[1].location: [5.0, 10.6, 8.4, 2.8, 134.8]}
        calc_statistics = self.pgreport._calc_statistics()
        self.assertEquals(calc_statistics[self.problems[0].location]["mean"], 8.0)
        self.assertEquals(calc_statistics[self.problems[0].location]["median"], 5.6)
        self.assertEquals(calc_statistics[self.problems[0].location]["variance"], 45.6)
        self.assertEquals(
            calc_statistics[self.problems[0].location]["standard_deviation"], 6.753)

        self.assertEquals(calc_statistics[self.problems[1].location]["mean"], 32.32)
        self.assertEquals(calc_statistics[self.problems[1].location]["median"], 8.4)
        self.assertEquals(calc_statistics[self.problems[1].location]["variance"], 2632.778)
        self.assertEquals(
            calc_statistics[self.problems[1].location]["standard_deviation"], 51.311)

    def test_get_correctmap(self):
        corrects = self.pgreport._get_correctmap(self.problems[0])
        self.assertEquals(
            corrects, {
                unicode(self.problems[0].location) + "_2_1": 1,
                unicode(self.problems[0].location) + "_2_2": 0
            }
        )

    def test_get_student_answers(self):
        answers1 = self.pgreport._get_student_answers(self.problems[0])
        self.problems[1].student_answers = {
            unicode(self.problems[1].location) + "_2_1": ["answer1", "answer2", 5]
        }
        answers2 = self.pgreport._get_student_answers(self.problems[1])

        self.assertEquals(
            answers1, {
                unicode(self.problems[0].location) + "_2_1": {"Correct": 1},
                unicode(self.problems[0].location) + "_2_2": {"Incorrect": 1}
            }
        )
        self.assertEquals(answers2, {
            unicode(self.problems[1].location) + "_2_1": ANY})
        self.assertEquals(
            answers2[unicode(self.problems[1].location) + "_2_1"],
            {"answer1": 1, 5: 1, "answer2": 1}
        )

    def test_get_module_data(self):
        module_mock = MagicMock()
        module_data = self.pgreport._get_module_data(module_mock)
        self.assertEquals(module_data, {
            'start': module_mock.start,
            'display_name': module_mock.display_name,
            'student_answers': {},
            'weight': module_mock.weight,
            'correct_map': {},
            'type': module_mock.category,
            'due': module_mock.due,
            'score/total': module_mock.get_progress()
        })

    def test_increment_student_answers(self):
        name = unicode(self.problems[0].location)
        unit_id1 = name + "_2_1"
        unit_id2 = name + "_2_2"
        unit_id3 = name + "_2_3"
        answer = {"Correct": 1}
        self.pgreport.module_summary[name] = {
            "student_answers": {
                unit_id1: {"Correct": 1}, unit_id2: {"Incorrect": 1}},
        }

        self.pgreport._increment_student_answers(name, answer, unit_id1)
        self.pgreport._increment_student_answers(name, answer, unit_id2)
        self.pgreport._increment_student_answers(name, answer, unit_id3)
        self.assertEquals(self.pgreport.module_summary[name]["student_answers"], {
            unit_id1: {"Correct": 2},
            unit_id2: {"Correct": 1, "Incorrect": 1},
            unit_id3: {"Correct": 1}})

    def test_increment_student_correctmap(self):
        name = unicode(self.problems[0].location)
        unit_id1 = name + "_2_1"
        unit_id2 = name + "_2_2"
        unit_id3 = name + "_2_3"
        self.pgreport.module_summary[name] = {
            "correct_map": {unit_id1: 1, unit_id2: 2},
        }
        self.pgreport._increment_student_correctmap(name, 1, unit_id1)
        self.pgreport._increment_student_correctmap(name, 1, unit_id2)
        self.pgreport._increment_student_correctmap(name, 1, unit_id3)
        self.assertEquals(self.pgreport.module_summary[name]["correct_map"], {
            unit_id1: 2, unit_id2: 3, unit_id3: 1})

    def test_collect_module_summary(self):
        module_mock = MagicMock()
        progress_mock = MagicMock()
        progress_mock.frac.return_value = (2.0, 3.0)
        module_mock.get_progress.return_value = progress_mock
        module_mock.location = self.problems[0].location

        self.pgreport.collect_module_summary(module_mock)
        self.assertEquals(self.pgreport.module_summary[module_mock.location], {
            'count': 1,
            'display_name': module_mock.display_name,
            'weight': module_mock.weight,
            'type': module_mock.category,
            'total_score': 3.0,
            'due': module_mock.due,
            'score/total': progress_mock,
            'submit_count': 1,
            'start': module_mock.start,
            'student_answers': {},
            'max_score': 2.0,
            'correct_map': {}
        })

        module_mock.is_submitted.return_value = False
        module_data = {
            "student_answers": {
                unicode(module_mock.location) + "_2_1": {"Correct": 1},
                unicode(module_mock.location) + "_2_2": [{"answer1": 1}, {"answer2": 2}]},
            "correct_map": {
                unicode(module_mock.location) + "_2_1": 1,
                unicode(module_mock.location) + "_2_2": 2}
        }

        with patch(
            'pgreport.views.ProgressReport._get_module_data',
            return_value=module_data
        ) as pgmock:
            self.pgreport.collect_module_summary(module_mock)

        self.assertEquals(
            self.pgreport.module_summary[module_mock.location], {
                'count': 2,
                'display_name': module_mock.display_name,
                'weight': module_mock.weight,
                'type': module_mock.category,
                'total_score': 6.0,
                'due': module_mock.due,
                'score/total': progress_mock,
                'submit_count': 1,
                'start': module_mock.start,
                'student_answers': {
                    unicode(module_mock.location) + '_2_1': {'Correct': 1},
                    unicode(module_mock.location) + '_2_2': {'answer1': 1, 'answer2': 2}
                },
                'max_score': 4.0,
                'correct_map': module_data["correct_map"]
            }
        )

    def test_yield_student_summary(self):
        module_mock = MagicMock()
        module_mock.location = self.problems[0].location

        csvheader = [
            'username', 'location', 'last_login', 'grade', 'percent',
            'start', 'display_name', 'student_answers', 'weight', 'correct_map',
            'type', 'due', 'score/total'
        ]
        rows = []
        mg = MagicMock()
        location_list = {
            u'chapter': [self.chapter.location],
            u'problem': [self.problems[0].location],
            u'sequential': [self.section.location],
            u'vertical': [self.vertical.location]
        }

        grade_mock = MagicMock(return_value={'grade': True, 'percent': 1.0})
        with nested(
            patch('pgreport.views.grades'),
            patch('pgreport.views.get_module_for_student',
                side_effect=[module_mock, module_mock]),
        ) as (grmock, gemock):
            grmock.grade = grade_mock
            #self.pgreport.update_state = lambda state: state
            self.pgreport.students = User.objects.filter(id__in=[1, 2])
            self.pgreport.location_list = location_list
            for row in self.pgreport.yield_students_progress():
                rows.append(row)

        def create_csvrow(csvrows):
            for i in [0, 1]:
                csvrows.append([
                    unicode(self.students[i].username), self.problems[0].location,
                    self.students[i].last_login.strftime("%Y/%m/%d %H:%M:%S %Z"),
                    True, 1.0, module_mock.start, module_mock.display_name,
                    {}, module_mock.weight, {}, module_mock.category,
                    module_mock.due, module_mock.get_progress(),
                ])
            return csvrows

        grmock.grade.assert_called_with(ANY, ANY, ANY)
        gemock.assert_called_with(ANY, ANY)
        self.assertEquals(rows, create_csvrow([csvheader]))

    """
    def test_yield_student_summary_with_update_state(self):
        module_mock = MagicMock()
        module_mock.location = self.problems[0].location

        csvheader = [
            'username', 'location', 'last_login', 'grade', 'percent',
            'start', 'display_name', 'student_answers', 'weight', 'correct_map',
            'type', 'due', 'score/total'
        ]
        rows = []
        mg = MagicMock()
        location_list = {
            u'chapter': [self.chapter.location],
            u'problem': [self.problems[0].location],
            u'sequential': [self.section.location],
            u'vertical': [self.vertical.location]
        }

        grade_mock = MagicMock(return_value={'grade': True, 'percent': 1.0})
        with nested(
            patch('pgreport.views.grades'),
            patch(
                'pgreport.views.get_module_for_student',
                side_effect=[module_mock, module_mock]
            ),
        ) as (grmock, gemock):
            grmock.grade = grade_mock
            self.pgreport.update_state = lambda state: state
            self.pgreport.students = User.objects.filter(id__in=[1, 2])
            self.pgreport.location_list = location_list
            for row in self.pgreport.yield_students_progress():
                rows.append(row)

        def create_csvrow(csvrows):
            for i in [0, 1]:
                csvrows.append([
                    unicode(self.students[i].username), self.problems[0].location,
                    self.students[i].last_login.strftime("%Y/%m/%d %H:%M:%S %Z"),
                    True, 1.0, module_mock.start, module_mock.display_name,
                    {}, module_mock.weight, {}, module_mock.category,
                    module_mock.due, module_mock.get_progress(),
                ])
            return csvrows

        grmock.grade.assert_called_with(ANY, ANY, ANY)
        gemock.assert_called_with(ANY, ANY, ANY)
        self.assertEquals(rows, create_csvrow([csvheader]))
    """

    def test_get_children_rec(self):
        course_mock = MagicMock()
        course_mock.location = self.course.location
        chapter_mock = MagicMock()
        chapter_mock.has_children = True
        chapter_mock.category = self.chapter.category
        chapter_mock.location = self.chapter.location
        chapter_mock.display_name = self.chapter.display_name
        sequential_mock = MagicMock()
        sequential_mock.has_children = True
        sequential_mock.category = self.section.category
        sequential_mock.location = self.section.location
        sequential_mock.display_name = self.section.display_name
        vertical_mock = MagicMock()
        vertical_mock.has_children = True
        vertical_mock.category = self.vertical.category
        vertical_mock.location = self.vertical.location
        vertical_mock.display_name = self.vertical.display_name

        chapter_mock.get_children.return_value = [sequential_mock]
        sequential_mock.get_children.return_value = [vertical_mock]
        vertical_mock.get_children.return_value = self.problems
        course_mock.get_children.return_value = [chapter_mock]

        self.pgreport._get_children_rec(course_mock)

        self.assertEquals(self.pgreport.location_list, {
            u'chapter': [self.chapter.location],
            u'problem': [self.problems[0].location, self.problems[1].location],
            u'sequential': [self.section.location],
            u'vertical': [self.vertical.location]
        })

        self.assertEquals(self.pgreport.location_parent, [
            {
                self.problems[0].location: [
                    self.chapter.display_name,
                    self.section.display_name,
                    self.vertical.display_name
                ]
            },
            {
                self.problems[1].location: [
                    self.chapter.display_name,
                    self.section.display_name,
                    self.vertical.display_name
                ]
            },
        ])

    @patch('sys.stdout', new_callable=StringIO.StringIO)
    @patch('pgreport.views.cache')
    @patch('pgreport.views.ProgressReport.collect_module_summary')
    def test_get_raw(self, cmmock, camock, symock):
        with self.assertRaises(InvalidCommand):
            self.pgreport.get_raw(command="fake")

        summary = self.pgreport2.get_raw(command="summary")
        self.assertEquals(summary, {
            'enrollments': 7, 'active_students': 6, 'module_tree': []})

        location_list = {
            u'chapter': [self.chapter.location],
            u'problem': [self.problems[0].location, self.problems[1].location],
            u'sequential': [self.section.location],
            u'vertical': [self.vertical.location]
        }
        module_summary = {'module_summary': {'dummy': 'dummy'}}

        mg = MagicMock()
        with nested(
            patch('pgreport.views.grades', return_value={'grade': True, 'percent': 1.0}),
            patch('pgreport.views.get_module_for_student', side_effect=[
                None, mg, mg, mg, mg, mg, mg, mg, mg, mg, mg, mg, mg, mg]),
        ) as (grmock, gemock):
            self.pgreport.location_list = location_list
            self.pgreport.module_summary = module_summary
            modules = self.pgreport.get_raw(command="modules")

        with nested(
            patch('pgreport.views.grades', return_value={'grade': True, 'percent': 1.0}),
            patch('pgreport.views.get_module_for_student', side_effect=[
                None, mg, mg, mg, mg, mg, mg, mg, mg, mg, mg, mg, mg, mg]),
        ) as (grmock, gemock):
            self.pgreport.location_list = location_list
            self.pgreport.module_summary = module_summary
            summary, modules = self.pgreport.get_raw()

        grmock.grade.assert_called_with(self.students[6], ANY, ANY)
        gemock.assert_any_called_with(self.students[6], self.course, self.problems[0].location)

    def test_get_pgreport_csv(self):
        gzipdata = gzip.GzipFile(fileobj=self.gzipfile, mode='wb')
        gzipdata.write("row1\nrow2\nrow3\n")
        gzipdata.close()

        scontent_mock = MagicMock()
        cstore_mock = MagicMock()
        content_mock = MagicMock()
        content_mock.stream_data.return_value = self.gzipfile.getvalue()
        cstore_mock.find.return_value = content_mock

        with nested(
            patch('pgreport.views.StaticContent', return_value=scontent_mock),
            patch('pgreport.views.contentstore', return_value=cstore_mock),
            patch('sys.stdout', new_callable=StringIO.StringIO)
        ) as (smock, cmock, stdmock):

            get_pgreport_csv(self.course.id)

        smock.compute_location.assert_called_once_with(ANY, "progress_students.csv.gz")
        cmock.assert_called_once_with()
        cmock.return_value.find.assert_called_once_with(ANY, throw_on_not_found=True, as_stream=True)
        content_mock.stream_data.assert_called_once_with()
        self.assertEquals(stdmock.getvalue(), 'row1\nrow2\nrow3\n')

        cstore_mock.find.side_effect = NotFoundError()
        with patch('pgreport.views.contentstore', return_value=cstore_mock):
            with self.assertRaises(NotFoundError):
                get_pgreport_csv(self.course.id)

    def test_create_pgreport_csv(self):
        rows = [
            ["username", "loc", "last_login"],
            [self.students[0].username, unicode(self.problems[0].location), "2014/1/1"],
            [self.students[1].username, unicode(self.problems[1].location), "2014/1/1"],
        ]

        progress_mock = MagicMock()
        progress_mock.get_raw.return_value = rows
        scontent_mock = MagicMock()
        cstore_mock = MagicMock()
        cstore_mock.fs.new_file().__exit__.return_value = False

        with nested(
            patch('pgreport.views.StaticContent', return_value=scontent_mock),
            patch('pgreport.views.contentstore', return_value=cstore_mock),
            patch('pgreport.views.ProgressReport', return_value=progress_mock),
        ) as (smock, cmock, pmock):
            create_pgreport_csv(self.course.id)

        smock.compute_location.assert_called_once_with(ANY, "progress_students.csv.gz")
        cmock.assert_called_once_with()
        cmock.return_value.find.assert_called_once_with(ANY)
        cmock.return_value.find.return_value.get_id.assert_called_once_with()

        progress_mock.get_raw.return_value = rows
        cstore_mock.fs.new_file().__enter__().write.side_effect = GridFSError()
        with nested(
            patch('pgreport.views.StaticContent', return_value=scontent_mock),
            patch('pgreport.views.contentstore', return_value=cstore_mock),
            patch('pgreport.views.ProgressReport', return_value=progress_mock),
        ) as (smock, cmock, pmock):
            with self.assertRaises(GridFSError):
                create_pgreport_csv(self.course.id)

    def test_delete_pgreport_csv(self):
        cstore_mock = MagicMock()
        content_mock = MagicMock()

        with nested(
            patch('pgreport.views.StaticContent', return_value=content_mock),
            patch('pgreport.views.contentstore', return_value=cstore_mock),
        ) as (scmock, csmock):
            delete_pgreport_csv(self.course.id)

        scmock.compute_location.assert_called_once_with(ANY, "progress_students.csv.gz")
        csmock.assert_called_once_with()
        csmock.return_value.find.assert_called_once_with(ANY)
        csmock.return_value.delete.assert_called_once_with(ANY)

    def test_get_pgreport_table(self):
        module_summary = {
            'location': unicode(self.problems[0].location),
            'count': 1,
            'display_name': "display_name",
            'weight': "weight",
            'type': "category",
            'total_score': 3.0,
            'due': "due",
            'score/total': "score-total",
            'submit_count': 1,
            'start': "start",
            'student_answers': {},
            'max_score': 2.0,
            'correct_map': {}
        }
        filter_mock = MagicMock()
        pgmodule_mock = MagicMock()
        filter_mock.values.return_value = [module_summary]
        pgmodule_mock.objects.filter.return_value = filter_mock

        with patch('pgreport.views.ProgressModules', pgmodule_mock):
            summary, modules = get_pgreport_table(self.course.id)

        filter_mock.values.assert_called_once_with()
        pgmodule_mock.objects.filter.assert_called_with(course_id=self.course.id)

        self.assertEquals(summary, {
            'enrollments': 7, 'active_students': 6,
            'module_tree': [
                {self.html.location: [u'Week 1', u'Lesson 1', u'Unit1']},
                {self.problems[0].location: [u'Week 1', u'Lesson 1', u'Unit1']},
                {self.problems[1].location: [u'Week 1', u'Lesson 1', u'Unit1']}
            ]
        })
        self.assertEquals(modules, {unicode(self.problems[0].location): module_summary})

    def test_update_pgreport_table(self):
        with patch('pgreport.views.ProgressModules') as pmock:
            update_pgreport_table(self.course.id)

        pmock.assert_any_call(
            count=6, display_name=self.problems[0].display_name,
            weight=None, standard_deviation=0.0, correct_map={}, median=0.0, due=None,
            submit_count=0, start=datetime.datetime(2030, 1, 1, 0, 0, tzinfo=UTC),
            location=self.problems[0].location, course_id=self.course.id, variance=0.0,
            student_answers={}, max_score=0.0, total_score=12.0, mean=0.0
        )

        with patch('pgreport.views.ProgressModules', side_effect=DatabaseError()):
            with self.assertRaises(DatabaseError):
                update_pgreport_table(self.course.id)


class ProgressModulesFactory(DjangoModelFactory):
    FACTORY_FOR = ProgressModules
    location = "i4x://org/cn/problem/unitid"
    course_id = "org/cn/run"
    created = datetime.datetime.now()
    display_name = "problem unit"
    module_type = "problem"
    count = 2
    max_score = 1
    total_score = 2
    submit_count = 1
    weight = None
    start = datetime.datetime.now()
    due = None
    correct_map = {u'i4x-org-cn-problem-unitid_2_1': 1}
    student_answers = {u'i4x-org-cn-problem-unitid_2_1': {
        u'choice_0': 1, u'choice_2': 1}}
    mean = 0.5
    median = 0.5
    variance = 0.25
    standard_deviation = 0.5


class ProgressModulesHistoryFactory(DjangoModelFactory):
    FACTORY_FOR = ProgressModulesHistory
    progress_module = factory.SubFactory(ProgressModulesFactory)
    created = datetime.datetime.now()
    count = 2
    max_score = 1
    total_score = 2
    submit_count = 1
    weight = None
    start = datetime.datetime.now()
    due = None
    correct_map = {u'i4x-org-cn-problem-unitid_2_1': 1}
    student_answers = {u'i4x-org-cn-problem-unitid_2_1': {
        u'choice_0': 1, u'choice_2': 1}}
    mean = 0.5
    median = 0.5
    variance = 0.25
    standard_deviation = 0.5


class ProgressModulesTestCase(TestCase):
    def setUp(self):
        self.start = self.created = datetime.datetime.utcnow()
        self.pgmodule = ProgressModulesFactory.create(
            start=self.start, created=self.created)

        patcher = patch('pgreport.views.logging')
        self.log_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        pass

    def test_repr(self):
        self.assertEquals(
            str(self.pgmodule),
            "[ProgressModules] i4x://org/cn/problem/unitid"
        )

    def test_unicode(self):
        self.assertEquals(
            unicode(self.pgmodule),
            "[ProgressModules] i4x://org/cn/problem/unitid"
        )

    def test_get_by_course_id(self):
        loc = "i4x://org/cn/problem/unitid"
        modules = ProgressModules.get_by_course_id(CourseLocator.from_string("org/cn/run"))
        self.assertEquals(modules[loc]["count"], 2)
        self.assertEquals(modules[loc]["display_name"], u'problem unit')
        self.assertEquals(modules[loc]["weight"], None)
        self.assertEquals(modules[loc]["standard_deviation"], 0.5)
        self.assertEquals(modules[loc]["total_score"], 2.0)
        self.assertEquals(modules[loc]["median"], 0.5)
        self.assertEquals(modules[loc]["due"], None)
        self.assertEquals(modules[loc]["submit_count"], 1)
        self.assertEquals(modules[loc]["module_type"], u'problem')
        self.assertEquals(modules[loc]["course_id"], u'org/cn/run')
        self.assertEquals(modules[loc]["variance"], 0.25)
        self.assertEquals(modules[loc]["student_answers"], u"{u'i4x-org-cn-problem-unitid_2_1': {u'choice_0': 1, u'choice_2': 1}}")
        self.assertEquals(modules[loc]["max_score"], 1.0)
        self.assertEquals(modules[loc]["correct_map"], u"{u'i4x-org-cn-problem-unitid_2_1': 1}")
        self.assertEquals(modules[loc]["mean"], 0.5)


class ProgressModulesHistoryTestCase(TestCase):
    def setUp(self):
        self.maxDiff = 10000
        self.start = self.created = datetime.datetime.utcnow()
        self.phmodule = ProgressModulesHistoryFactory.create(
            start=self.start, created=self.created)

        patcher = patch('pgreport.views.logging')
        self.log_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def tearDown(self):
        pass

    def test_repr(self):
        self.assertEquals(
            str(self.phmodule),
            "[ProgressModules] i4x://org/cn/problem/unitid : created {}".format(self.created)
        )

    def test_unicode(self):
        self.assertEquals(
            unicode(self.phmodule),
            "[ProgressModules] i4x://org/cn/problem/unitid : created {}".format(self.created)
        )
