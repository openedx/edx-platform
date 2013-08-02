import json
from datetime import datetime
from pytz import UTC
from StringIO import StringIO

from django.test import TestCase
from django.test.utils import override_settings
from django.core import management

from courseware.tests.tests import TEST_DATA_MONGO_MODULESTORE
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from courseware.tests.factories import StudentModuleFactory
from queryable_student_module.models import Log, StudentModuleExpand
from capa.tests.response_xml_factory import StringResponseXMLFactory


@override_settings(MODULESTORE=TEST_DATA_MONGO_MODULESTORE)
class TestPopulateStudentModuleExpand(TestCase):

    def setUp(self):
        self.command = 'populate_studentmoduleexpand'
        self.script_id = "studentmoduleexpand"
        #self.course_id = 'test/test/test'
        
        self.course = CourseFactory.create()
        
        section = ItemFactory.create(
            parent_location=self.course.location,
            category="chapter",
            display_name="test factory section",
        )
        sub_section = ItemFactory.create(
            parent_location=section.location,
            category="sequential",
           # metadata={'graded': True, 'format': 'Homework'}
        )
    
        unit = ItemFactory.create(
            parent_location=sub_section.location,
            category="vertical",
            metadata={'graded': True, 'format': 'Homework'}
        )
        
        category = "problem"
        self.item = ItemFactory.create(
            parent_location=unit.location,
            category=category,
            data=StringResponseXMLFactory().build_xml(answer='foo'),
            metadata={'rerandomize': 'always'}
        )

        self.item2 = ItemFactory.create(
            parent_location=unit.location,
            category=category,
            data=StringResponseXMLFactory().build_xml(answer='foo'),
            metadata={'rerandomize': 'always'}
        )

    def test_missing_input(self):
        """
        Fails safely when not given enough input
        """
        try:
            management.call_command(self.command)
            self.assertTrue(True)
        except:
            self.assertTrue(False)

    def test_just_logs_if_empty_course(self):
        """
        If the course has nothing in it, just logs the run in the log table
        """
        management.call_command(self.command, self.course.id)

        self.assertEqual(len(Log.objects.filter(script_id__exact=self.script_id, course_id__exact=self.course.id)), 1)
        self.assertEqual(len(StudentModuleExpand.objects.filter(course_id__exact=self.course.id)), 0)

    def test_force_update(self):
        """
        Even if there is a log entry for incremental update, force a full update

        This may be done because something happened in the last update.
        """

        # Create a StudentModule that is before the log entry
        sm = StudentModuleFactory(
            course_id=self.course.id,
            module_type='problem',
            grade=1,
            max_grade=1,
            state=json.dumps({'attempts': 1}),
            module_state_key=self.item.location
        )

        # Create the log entry
        log = Log(script_id=self.script_id, course_id=self.course.id, created=datetime.now(UTC))
        log.save()

        # Create a StudentModuleExpand that is after the log entry and has a different attempts value
        sme = StudentModuleExpand(
            course_id=self.course.id,
            module_state_key=sm.module_state_key,
            student_module_id=sm.id,
            attempts=0,
        )

        # Call command with the -f flag
        management.call_command(self.command, self.course.id, force=True)

        # Check to see if new rows have been added
        self.assertEqual(len(Log.objects.filter(script_id__exact=self.script_id, course_id__exact=self.course.id)), 2)
        self.assertEqual(len(StudentModuleExpand.objects.filter(course_id__exact=self.course.id)), 1)
        self.assertEqual(StudentModuleExpand.objects.filter(course_id__exact=self.course.id)[0].attempts, 1)

    def test_incremental_update_if_log_exists(self):
        """
        Make sure it uses the log entry if it exists and we aren't forcing a full update
        """
        # Create a StudentModule that is before the log entry
        sm = StudentModuleFactory(
            course_id=self.course.id,
            module_type='problem',
            grade=1,
            max_grade=1,
            state=json.dumps({'attempts': 1}),
            module_state_key=self.item.location
        )

        # Create the log entry
        log = Log(script_id=self.script_id, course_id=self.course.id, created=datetime.now(UTC))
        log.save()

        # Create a StudentModule that is after the log entry
        sm = StudentModuleFactory(
            course_id=self.course.id,
            module_type='problem',
            grade=1,
            max_grade=1,
            state=json.dumps({'attempts': 1}),
            module_state_key=self.item.location
        )

        # Call command
        management.call_command(self.command, self.course.id)

        # Check to see if new row has been added to log
        self.assertEqual(len(Log.objects.filter(script_id__exact=self.script_id, course_id__exact=self.course.id)), 2)

        # Even though there are two studentmodules only one row should be created
        self.assertEqual(len(StudentModuleExpand.objects.filter(course_id__exact=self.course.id)), 1)

    def test_update_only_if_row_modified(self):
        """
        Test populate does not update a row if it is not necessary
        For example the problem may have a more recent modified date but the attempts value has not changed.
        """

        self.assertEqual(len(StudentModuleExpand.objects.filter(course_id__exact=self.course.id)), 0)

        # Create a StudentModule
        sm1 = StudentModuleFactory(
            course_id=self.course.id,
            module_type='problem',
            grade=1,
            max_grade=1,
            module_state_key=self.item.location
        )
        # Create a StudentModuleExpand
        sme1 = StudentModuleExpand(
            course_id=self.course.id,
            student_module_id=sm1.id,
            module_state_key=sm1.module_state_key,
            student_id=sm1.student.id,
            attempts=0,
        )
        sme1.save()

        # Touch the StudentModule row so it has a later modified time
        sm1.state = json.dumps({'attempts': 1})
        sm1.save()

        # Create a StudentModule
        sm2 = StudentModuleFactory(
            course_id=self.course.id,
            module_type='problem',
            module_state_key=self.item2.location,
            grade=1,
            max_grade=1,
            state=json.dumps({'attempts': 2}),
        )
        # Create a StudentModuleExpand that has the same attempts value
        sme2 = StudentModuleExpand(
            course_id=self.course.id,
            student_module_id=sm2.id,
            module_state_key=sm2.module_state_key,
            student_id=sm2.student.id,
            attempts=2,
        )
        sme2.save()

        self.assertEqual(len(StudentModuleExpand.objects.filter(course_id__exact=self.course.id)), 2)

        # Call command
        management.call_command(self.command, self.course.id)

        self.assertEqual(len(StudentModuleExpand.objects.filter(
                         course_id__exact=self.course.id, module_state_key__exact=sme1.module_state_key)), 1)
        self.assertEqual(len(StudentModuleExpand.objects.filter(
                         course_id__exact=self.course.id, module_state_key__exact=sme2.module_state_key)), 1)

        self.assertEqual(StudentModuleExpand.objects.filter(
                         course_id__exact=self.course.id, module_state_key__exact=sme1.module_state_key)[0].attempts, 1)
        self.assertEqual(StudentModuleExpand.objects.filter(
                         course_id__exact=self.course.id, module_state_key__exact=sme2.module_state_key)[0].attempts, 2)
