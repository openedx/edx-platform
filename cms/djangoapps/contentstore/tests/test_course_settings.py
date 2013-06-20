"""
Tests for Studio Course Settings.
"""
import datetime
import json
import copy
import mock

from django.contrib.auth.models import User
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.utils.timezone import UTC
from django.test.utils import override_settings

from xmodule.modulestore import Location
from models.settings.course_details import (CourseDetails, CourseSettingsEncoder)
from models.settings.course_grading import CourseGradingModel
from contentstore.utils import get_modulestore

from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory

from models.settings.course_metadata import CourseMetadata
from xmodule.modulestore.xml_importer import import_from_xml
from xmodule.fields import Date


class CourseTestCase(ModuleStoreTestCase):
    """
    Base class for test classes below.
    """
    def setUp(self):
        """
        These tests need a user in the DB so that the django Test Client
        can log them in.
        They inherit from the ModuleStoreTestCase class so that the mongodb collection
        will be cleared out before each test case execution and deleted
        afterwards.
        """
        uname = 'testuser'
        email = 'test+courses@edx.org'
        password = 'foo'

        # Create the use so we can log them in.
        self.user = User.objects.create_user(uname, email, password)

        # Note that we do not actually need to do anything
        # for registration if we directly mark them active.
        self.user.is_active = True
        # Staff has access to view all courses
        self.user.is_staff = True
        self.user.save()

        self.client = Client()
        self.client.login(username=uname, password=password)

        course = CourseFactory.create(template='i4x://edx/templates/course/Empty', org='MITx', number='999', display_name='Robot Super Course')
        self.course_location = course.location


class CourseDetailsTestCase(CourseTestCase):
    """
    Tests the first course settings page (course dates, overview, etc.).
    """
    def test_virgin_fetch(self):
        details = CourseDetails.fetch(self.course_location)
        self.assertEqual(details.course_location, self.course_location, "Location not copied into")
        self.assertIsNotNone(details.start_date.tzinfo)
        self.assertIsNone(details.end_date, "end date somehow initialized " + str(details.end_date))
        self.assertIsNone(details.enrollment_start, "enrollment_start date somehow initialized " + str(details.enrollment_start))
        self.assertIsNone(details.enrollment_end, "enrollment_end date somehow initialized " + str(details.enrollment_end))
        self.assertIsNone(details.syllabus, "syllabus somehow initialized" + str(details.syllabus))
        self.assertEqual(details.overview, "", "overview somehow initialized" + details.overview)
        self.assertIsNone(details.intro_video, "intro_video somehow initialized" + str(details.intro_video))
        self.assertIsNone(details.effort, "effort somehow initialized" + str(details.effort))

    def test_encoder(self):
        details = CourseDetails.fetch(self.course_location)
        jsondetails = json.dumps(details, cls=CourseSettingsEncoder)
        jsondetails = json.loads(jsondetails)
        self.assertTupleEqual(Location(jsondetails['course_location']), self.course_location, "Location !=")
        self.assertIsNone(jsondetails['end_date'], "end date somehow initialized ")
        self.assertIsNone(jsondetails['enrollment_start'], "enrollment_start date somehow initialized ")
        self.assertIsNone(jsondetails['enrollment_end'], "enrollment_end date somehow initialized ")
        self.assertIsNone(jsondetails['syllabus'], "syllabus somehow initialized")
        self.assertEqual(jsondetails['overview'], "", "overview somehow initialized")
        self.assertIsNone(jsondetails['intro_video'], "intro_video somehow initialized")
        self.assertIsNone(jsondetails['effort'], "effort somehow initialized")

    def test_ooc_encoder(self):
        """
        Test the encoder out of its original constrained purpose to see if it functions for general use
        """
        details = {'location': Location(['tag', 'org', 'course', 'category', 'name']),
                   'number': 1,
                   'string': 'string',
                   'datetime': datetime.datetime.now(UTC())}
        jsondetails = json.dumps(details, cls=CourseSettingsEncoder)
        jsondetails = json.loads(jsondetails)

        self.assertIn('location', jsondetails)
        self.assertIn('org', jsondetails['location'])
        self.assertEquals('org', jsondetails['location'][1])
        self.assertEquals(1, jsondetails['number'])
        self.assertEqual(jsondetails['string'], 'string')

    def test_update_and_fetch(self):
        # # NOTE: I couldn't figure out how to validly test time setting w/ all the conversions
        jsondetails = CourseDetails.fetch(self.course_location)
        jsondetails.syllabus = "<a href='foo'>bar</a>"
        # encode - decode to convert date fields and other data which changes form
        self.assertEqual(
            CourseDetails.update_from_json(jsondetails.__dict__).syllabus,
            jsondetails.syllabus, "After set syllabus"
        )
        jsondetails.overview = "Overview"
        self.assertEqual(
            CourseDetails.update_from_json(jsondetails.__dict__).overview,
            jsondetails.overview, "After set overview"
        )
        jsondetails.intro_video = "intro_video"
        self.assertEqual(
            CourseDetails.update_from_json(jsondetails.__dict__).intro_video,
            jsondetails.intro_video, "After set intro_video"
        )
        jsondetails.effort = "effort"
        self.assertEqual(
            CourseDetails.update_from_json(jsondetails.__dict__).effort,
            jsondetails.effort, "After set effort"
        )

    @override_settings(MKTG_URLS={'ROOT': 'dummy-root'})
    def test_marketing_site_fetch(self):
        settings_details_url = reverse(
            'settings_details',
            kwargs={
                'org': self.course_location.org,
                'name': self.course_location.name,
                'course': self.course_location.course
            }
        )

        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {'ENABLE_MKTG_SITE': True}):
            response = self.client.get(settings_details_url)
            self.assertContains(response, "Course Summary Page")
            self.assertContains(response, "course summary page will not be viewable")

            self.assertContains(response, "Course Start Date")
            self.assertContains(response, "Course End Date")
            self.assertNotContains(response, "Enrollment Start Date")
            self.assertNotContains(response, "Enrollment End Date")
            self.assertContains(response, "not the dates shown on your course summary page")

            self.assertNotContains(response, "Introducing Your Course")
            self.assertNotContains(response, "Requirements")

    def test_regular_site_fetch(self):
        settings_details_url = reverse(
            'settings_details',
            kwargs={
                'org': self.course_location.org,
                'name': self.course_location.name,
                'course': self.course_location.course
            }
        )

        with mock.patch.dict('django.conf.settings.MITX_FEATURES', {'ENABLE_MKTG_SITE': False}):
            response = self.client.get(settings_details_url)
            self.assertContains(response, "Course Summary Page")
            self.assertNotContains(response, "course summary page will not be viewable")

            self.assertContains(response, "Course Start Date")
            self.assertContains(response, "Course End Date")
            self.assertContains(response, "Enrollment Start Date")
            self.assertContains(response, "Enrollment End Date")
            self.assertNotContains(response, "not the dates shown on your course summary page")

            self.assertContains(response, "Introducing Your Course")
            self.assertContains(response, "Requirements")


class CourseDetailsViewTest(CourseTestCase):
    """
    Tests for modifying content on the first course settings page (course dates, overview, etc.).
    """
    def alter_field(self, url, details, field, val):
        setattr(details, field, val)
        # Need to partially serialize payload b/c the mock doesn't handle it correctly
        payload = copy.copy(details.__dict__)
        payload['course_location'] = details.course_location.url()
        payload['start_date'] = CourseDetailsViewTest.convert_datetime_to_iso(details.start_date)
        payload['end_date'] = CourseDetailsViewTest.convert_datetime_to_iso(details.end_date)
        payload['enrollment_start'] = CourseDetailsViewTest.convert_datetime_to_iso(details.enrollment_start)
        payload['enrollment_end'] = CourseDetailsViewTest.convert_datetime_to_iso(details.enrollment_end)
        resp = self.client.post(url, json.dumps(payload), "application/json")
        self.compare_details_with_encoding(json.loads(resp.content), details.__dict__, field + str(val))

    @staticmethod
    def convert_datetime_to_iso(dt):
        return Date().to_json(dt)

    def test_update_and_fetch(self):
        details = CourseDetails.fetch(self.course_location)

        # resp s/b json from here on
        url = reverse('course_settings', kwargs={'org': self.course_location.org, 'course': self.course_location.course,
                                                 'name': self.course_location.name, 'section': 'details'})
        resp = self.client.get(url)
        self.compare_details_with_encoding(json.loads(resp.content), details.__dict__, "virgin get")

        utc = UTC()
        self.alter_field(url, details, 'start_date', datetime.datetime(2012, 11, 12, 1, 30, tzinfo=utc))
        self.alter_field(url, details, 'start_date', datetime.datetime(2012, 11, 1, 13, 30, tzinfo=utc))
        self.alter_field(url, details, 'end_date', datetime.datetime(2013, 2, 12, 1, 30, tzinfo=utc))
        self.alter_field(url, details, 'enrollment_start', datetime.datetime(2012, 10, 12, 1, 30, tzinfo=utc))

        self.alter_field(url, details, 'enrollment_end', datetime.datetime(2012, 11, 15, 1, 30, tzinfo=utc))
        self.alter_field(url, details, 'overview', "Overview")
        self.alter_field(url, details, 'intro_video', "intro_video")
        self.alter_field(url, details, 'effort', "effort")

    def compare_details_with_encoding(self, encoded, details, context):
        self.compare_date_fields(details, encoded, context, 'start_date')
        self.compare_date_fields(details, encoded, context, 'end_date')
        self.compare_date_fields(details, encoded, context, 'enrollment_start')
        self.compare_date_fields(details, encoded, context, 'enrollment_end')
        self.assertEqual(details['overview'], encoded['overview'], context + " overviews not ==")
        self.assertEqual(details['intro_video'], encoded.get('intro_video', None), context + " intro_video not ==")
        self.assertEqual(details['effort'], encoded['effort'], context + " efforts not ==")

    def compare_date_fields(self, details, encoded, context, field):
        if details[field] is not None:
            date = Date()
            if field in encoded and encoded[field] is not None:
                dt1 = date.from_json(encoded[field])
                dt2 = details[field]

                expected_delta = datetime.timedelta(0)
                self.assertEqual(dt1 - dt2, expected_delta, str(dt1) + "!=" + str(dt2) + " at " + context)
            else:
                self.fail(field + " missing from encoded but in details at " + context)
        elif field in encoded and encoded[field] is not None:
            self.fail(field + " included in encoding but missing from details at " + context)


class CourseGradingTest(CourseTestCase):
    """
    Tests for the course settings grading page.
    """
    def test_initial_grader(self):
        descriptor = get_modulestore(self.course_location).get_item(self.course_location)
        test_grader = CourseGradingModel(descriptor)
        # ??? How much should this test bake in expectations about defaults and thus fail if defaults change?
        self.assertEqual(self.course_location, test_grader.course_location, "Course locations")
        self.assertIsNotNone(test_grader.graders, "No graders")
        self.assertIsNotNone(test_grader.grade_cutoffs, "No cutoffs")

    def test_fetch_grader(self):
        test_grader = CourseGradingModel.fetch(self.course_location.url())
        self.assertEqual(self.course_location, test_grader.course_location, "Course locations")
        self.assertIsNotNone(test_grader.graders, "No graders")
        self.assertIsNotNone(test_grader.grade_cutoffs, "No cutoffs")

        test_grader = CourseGradingModel.fetch(self.course_location)
        self.assertEqual(self.course_location, test_grader.course_location, "Course locations")
        self.assertIsNotNone(test_grader.graders, "No graders")
        self.assertIsNotNone(test_grader.grade_cutoffs, "No cutoffs")

        for i, grader in enumerate(test_grader.graders):
            subgrader = CourseGradingModel.fetch_grader(self.course_location, i)
            self.assertDictEqual(grader, subgrader, str(i) + "th graders not equal")

        subgrader = CourseGradingModel.fetch_grader(self.course_location.list(), 0)
        self.assertDictEqual(test_grader.graders[0], subgrader, "failed with location as list")

    def test_fetch_cutoffs(self):
        test_grader = CourseGradingModel.fetch_cutoffs(self.course_location)
        # ??? should this check that it's at least a dict? (expected is { "pass" : 0.5 } I think)
        self.assertIsNotNone(test_grader, "No cutoffs via fetch")

        test_grader = CourseGradingModel.fetch_cutoffs(self.course_location.url())
        self.assertIsNotNone(test_grader, "No cutoffs via fetch with url")

    def test_fetch_grace(self):
        test_grader = CourseGradingModel.fetch_grace_period(self.course_location)
        # almost a worthless test
        self.assertIn('grace_period', test_grader, "No grace via fetch")

        test_grader = CourseGradingModel.fetch_grace_period(self.course_location.url())
        self.assertIn('grace_period', test_grader, "No cutoffs via fetch with url")

    def test_update_from_json(self):
        test_grader = CourseGradingModel.fetch(self.course_location)
        altered_grader = CourseGradingModel.update_from_json(test_grader.__dict__)
        self.assertDictEqual(test_grader.__dict__, altered_grader.__dict__, "Noop update")

        test_grader.graders[0]['weight'] = test_grader.graders[0].get('weight') * 2
        altered_grader = CourseGradingModel.update_from_json(test_grader.__dict__)
        self.assertDictEqual(test_grader.__dict__, altered_grader.__dict__, "Weight[0] * 2")

        test_grader.grade_cutoffs['D'] = 0.3
        altered_grader = CourseGradingModel.update_from_json(test_grader.__dict__)
        self.assertDictEqual(test_grader.__dict__, altered_grader.__dict__, "cutoff add D")

        test_grader.grace_period = {'hours': 4, 'minutes': 5, 'seconds': 0}
        altered_grader = CourseGradingModel.update_from_json(test_grader.__dict__)
        print test_grader.grace_period, altered_grader.grace_period
        self.assertDictEqual(test_grader.__dict__, altered_grader.__dict__, "4 hour grace period")

    def test_update_grader_from_json(self):
        test_grader = CourseGradingModel.fetch(self.course_location)
        altered_grader = CourseGradingModel.update_grader_from_json(test_grader.course_location, test_grader.graders[1])
        self.assertDictEqual(test_grader.graders[1], altered_grader, "Noop update")

        test_grader.graders[1]['min_count'] = test_grader.graders[1].get('min_count') + 2
        altered_grader = CourseGradingModel.update_grader_from_json(test_grader.course_location, test_grader.graders[1])
        self.assertDictEqual(test_grader.graders[1], altered_grader, "min_count[1] + 2")

        test_grader.graders[1]['drop_count'] = test_grader.graders[1].get('drop_count') + 1
        altered_grader = CourseGradingModel.update_grader_from_json(test_grader.course_location, test_grader.graders[1])
        self.assertDictEqual(test_grader.graders[1], altered_grader, "drop_count[1] + 2")


class CourseMetadataEditingTest(CourseTestCase):
    """
    Tests for CourseMetadata.
    """
    def setUp(self):
        CourseTestCase.setUp(self)
        # add in the full class too
        import_from_xml(get_modulestore(self.course_location), 'common/test/data/', ['full'])
        self.fullcourse_location = Location(['i4x', 'edX', 'full', 'course', '6.002_Spring_2012', None])

    def test_fetch_initial_fields(self):
        test_model = CourseMetadata.fetch(self.course_location)
        self.assertIn('display_name', test_model, 'Missing editable metadata field')
        self.assertEqual(test_model['display_name'], 'Robot Super Course', "not expected value")

        test_model = CourseMetadata.fetch(self.fullcourse_location)
        self.assertNotIn('graceperiod', test_model, 'blacklisted field leaked in')
        self.assertIn('display_name', test_model, 'full missing editable metadata field')
        self.assertEqual(test_model['display_name'], 'Testing', "not expected value")
        self.assertIn('rerandomize', test_model, 'Missing rerandomize metadata field')
        self.assertIn('showanswer', test_model, 'showanswer field ')
        self.assertIn('xqa_key', test_model, 'xqa_key field ')

    def test_update_from_json(self):
        test_model = CourseMetadata.update_from_json(self.course_location, {
            "advertised_start": "start A",
            "testcenter_info": {"c": "test"},
            "days_early_for_beta": 2
        })
        self.update_check(test_model)
        # try fresh fetch to ensure persistence
        test_model = CourseMetadata.fetch(self.course_location)
        self.update_check(test_model)
        # now change some of the existing metadata
        test_model = CourseMetadata.update_from_json(self.course_location, {
            "advertised_start": "start B",
            "display_name": "jolly roger"}
        )
        self.assertIn('display_name', test_model, 'Missing editable metadata field')
        self.assertEqual(test_model['display_name'], 'jolly roger', "not expected value")
        self.assertIn('advertised_start', test_model, 'Missing revised advertised_start metadata field')
        self.assertEqual(test_model['advertised_start'], 'start B', "advertised_start not expected value")

    def update_check(self, test_model):
        self.assertIn('display_name', test_model, 'Missing editable metadata field')
        self.assertEqual(test_model['display_name'], 'Robot Super Course', "not expected value")
        self.assertIn('advertised_start', test_model, 'Missing new advertised_start metadata field')
        self.assertEqual(test_model['advertised_start'], 'start A', "advertised_start not expected value")
        self.assertIn('testcenter_info', test_model, 'Missing testcenter_info metadata field')
        self.assertDictEqual(test_model['testcenter_info'], {"c": "test"}, "testcenter_info not expected value")
        self.assertIn('days_early_for_beta', test_model, 'Missing days_early_for_beta metadata field')
        self.assertEqual(test_model['days_early_for_beta'], 2, "days_early_for_beta not expected value")

    def test_delete_key(self):
        test_model = CourseMetadata.delete_key(self.fullcourse_location, {'deleteKeys': ['doesnt_exist', 'showanswer', 'xqa_key']})
        # ensure no harm
        self.assertNotIn('graceperiod', test_model, 'blacklisted field leaked in')
        self.assertIn('display_name', test_model, 'full missing editable metadata field')
        self.assertEqual(test_model['display_name'], 'Testing', "not expected value")
        self.assertIn('rerandomize', test_model, 'Missing rerandomize metadata field')
        # check for deletion effectiveness
        self.assertEqual('closed', test_model['showanswer'], 'showanswer field still in')
        self.assertEqual(None, test_model['xqa_key'], 'xqa_key field still in')
