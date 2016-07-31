"""
Tests for Studio Course Settings.
"""
import datetime
import ddt
import json
import copy
import mock
from mock import Mock, patch
import unittest

from django.conf import settings
from django.utils.timezone import UTC
from django.test.utils import override_settings

from contentstore.utils import reverse_course_url, reverse_usage_url
from models.settings.course_grading import CourseGradingModel
from models.settings.course_metadata import CourseMetadata
from models.settings.encoder import CourseSettingsEncoder
from openedx.core.djangoapps.self_paced.models import SelfPacedConfiguration
from openedx.core.djangoapps.models.course_details import CourseDetails
from student.roles import CourseInstructorRole, CourseStaffRole
from student.tests.factories import UserFactory
from xblock_django.models import XBlockStudioConfigurationFlag
from xmodule.fields import Date
from xmodule.modulestore import ModuleStoreEnum
from xmodule.modulestore.django import modulestore
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.tabs import InvalidTabsException
from milestones.tests.utils import MilestonesTestCaseMixin

from .utils import CourseTestCase, AjaxEnabledTestClient


def get_url(course_id, handler_name='settings_handler'):
    return reverse_course_url(handler_name, course_id)


class CourseSettingsEncoderTest(CourseTestCase):
    """
    Tests for CourseSettingsEncoder.
    """
    def test_encoder(self):
        details = CourseDetails.fetch(self.course.id)
        jsondetails = json.dumps(details, cls=CourseSettingsEncoder)
        jsondetails = json.loads(jsondetails)
        self.assertEqual(jsondetails['course_image_name'], self.course.course_image)
        self.assertIsNone(jsondetails['end_date'], "end date somehow initialized ")
        self.assertIsNone(jsondetails['enrollment_start'], "enrollment_start date somehow initialized ")
        self.assertIsNone(jsondetails['enrollment_end'], "enrollment_end date somehow initialized ")
        self.assertIsNone(jsondetails['syllabus'], "syllabus somehow initialized")
        self.assertIsNone(jsondetails['intro_video'], "intro_video somehow initialized")
        self.assertIsNone(jsondetails['effort'], "effort somehow initialized")
        self.assertIsNone(jsondetails['language'], "language somehow initialized")

    def test_pre_1900_date(self):
        """
        Tests that the encoder can handle a pre-1900 date, since strftime
        doesn't work for these dates.
        """
        details = CourseDetails.fetch(self.course.id)
        pre_1900 = datetime.datetime(1564, 4, 23, 1, 1, 1, tzinfo=UTC())
        details.enrollment_start = pre_1900
        dumped_jsondetails = json.dumps(details, cls=CourseSettingsEncoder)
        loaded_jsondetails = json.loads(dumped_jsondetails)
        self.assertEqual(loaded_jsondetails['enrollment_start'], pre_1900.isoformat())

    def test_ooc_encoder(self):
        """
        Test the encoder out of its original constrained purpose to see if it functions for general use
        """
        details = {
            'number': 1,
            'string': 'string',
            'datetime': datetime.datetime.now(UTC())
        }
        jsondetails = json.dumps(details, cls=CourseSettingsEncoder)
        jsondetails = json.loads(jsondetails)

        self.assertEquals(1, jsondetails['number'])
        self.assertEqual(jsondetails['string'], 'string')


@ddt.ddt
class CourseDetailsViewTest(CourseTestCase, MilestonesTestCaseMixin):
    """
    Tests for modifying content on the first course settings page (course dates, overview, etc.).
    """
    def setUp(self):
        super(CourseDetailsViewTest, self).setUp()

    def alter_field(self, url, details, field, val):
        """
        Change the one field to the given value and then invoke the update post to see if it worked.
        """
        setattr(details, field, val)
        # Need to partially serialize payload b/c the mock doesn't handle it correctly
        payload = copy.copy(details.__dict__)
        payload['start_date'] = CourseDetailsViewTest.convert_datetime_to_iso(details.start_date)
        payload['end_date'] = CourseDetailsViewTest.convert_datetime_to_iso(details.end_date)
        payload['enrollment_start'] = CourseDetailsViewTest.convert_datetime_to_iso(details.enrollment_start)
        payload['enrollment_end'] = CourseDetailsViewTest.convert_datetime_to_iso(details.enrollment_end)
        resp = self.client.ajax_post(url, payload)
        self.compare_details_with_encoding(json.loads(resp.content), details.__dict__, field + str(val))

    @staticmethod
    def convert_datetime_to_iso(datetime_obj):
        """
        Use the xblock serializer to convert the datetime
        """
        return Date().to_json(datetime_obj)

    def test_update_and_fetch(self):
        SelfPacedConfiguration(enabled=True).save()
        details = CourseDetails.fetch(self.course.id)

        # resp s/b json from here on
        url = get_url(self.course.id)
        resp = self.client.get_json(url)
        self.compare_details_with_encoding(json.loads(resp.content), details.__dict__, "virgin get")

        utc = UTC()
        self.alter_field(url, details, 'start_date', datetime.datetime(2012, 11, 12, 1, 30, tzinfo=utc))
        self.alter_field(url, details, 'start_date', datetime.datetime(2012, 11, 1, 13, 30, tzinfo=utc))
        self.alter_field(url, details, 'end_date', datetime.datetime(2013, 2, 12, 1, 30, tzinfo=utc))
        self.alter_field(url, details, 'enrollment_start', datetime.datetime(2012, 10, 12, 1, 30, tzinfo=utc))

        self.alter_field(url, details, 'enrollment_end', datetime.datetime(2012, 11, 15, 1, 30, tzinfo=utc))
        self.alter_field(url, details, 'short_description', "Short Description")
        self.alter_field(url, details, 'overview', "Overview")
        self.alter_field(url, details, 'intro_video', "intro_video")
        self.alter_field(url, details, 'effort', "effort")
        self.alter_field(url, details, 'course_image_name', "course_image_name")
        self.alter_field(url, details, 'language', "en")
        self.alter_field(url, details, 'self_paced', "true")

    def compare_details_with_encoding(self, encoded, details, context):
        """
        compare all of the fields of the before and after dicts
        """
        self.compare_date_fields(details, encoded, context, 'start_date')
        self.compare_date_fields(details, encoded, context, 'end_date')
        self.compare_date_fields(details, encoded, context, 'enrollment_start')
        self.compare_date_fields(details, encoded, context, 'enrollment_end')
        self.assertEqual(
            details['short_description'], encoded['short_description'], context + " short_description not =="
        )
        self.assertEqual(details['overview'], encoded['overview'], context + " overviews not ==")
        self.assertEqual(details['intro_video'], encoded.get('intro_video', None), context + " intro_video not ==")
        self.assertEqual(details['effort'], encoded['effort'], context + " efforts not ==")
        self.assertEqual(details['course_image_name'], encoded['course_image_name'], context + " images not ==")
        self.assertEqual(details['language'], encoded['language'], context + " languages not ==")

    def compare_date_fields(self, details, encoded, context, field):
        """
        Compare the given date fields between the before and after doing json deserialization
        """
        if details[field] is not None:
            date = Date()
            if field in encoded and encoded[field] is not None:
                dt1 = date.from_json(encoded[field])
                dt2 = details[field]

                self.assertEqual(dt1, dt2, msg="{} != {} at {}".format(dt1, dt2, context))
            else:
                self.fail(field + " missing from encoded but in details at " + context)
        elif field in encoded and encoded[field] is not None:
            self.fail(field + " included in encoding but missing from details at " + context)

    @mock.patch.dict("django.conf.settings.FEATURES", {'ENABLE_PREREQUISITE_COURSES': True, 'MILESTONES_APP': True})
    def test_pre_requisite_course_list_present(self):
        settings_details_url = get_url(self.course.id)
        response = self.client.get_html(settings_details_url)
        self.assertContains(response, "Prerequisite Course")

    @mock.patch.dict("django.conf.settings.FEATURES", {'ENABLE_PREREQUISITE_COURSES': True, 'MILESTONES_APP': True})
    def test_pre_requisite_course_update_and_fetch(self):
        url = get_url(self.course.id)
        resp = self.client.get_json(url)
        course_detail_json = json.loads(resp.content)
        # assert pre_requisite_courses is initialized
        self.assertEqual([], course_detail_json['pre_requisite_courses'])

        # update pre requisite courses with a new course keys
        pre_requisite_course = CourseFactory.create(org='edX', course='900', run='test_run')
        pre_requisite_course2 = CourseFactory.create(org='edX', course='902', run='test_run')
        pre_requisite_course_keys = [unicode(pre_requisite_course.id), unicode(pre_requisite_course2.id)]
        course_detail_json['pre_requisite_courses'] = pre_requisite_course_keys
        self.client.ajax_post(url, course_detail_json)

        # fetch updated course to assert pre_requisite_courses has new values
        resp = self.client.get_json(url)
        course_detail_json = json.loads(resp.content)
        self.assertEqual(pre_requisite_course_keys, course_detail_json['pre_requisite_courses'])

        # remove pre requisite course
        course_detail_json['pre_requisite_courses'] = []
        self.client.ajax_post(url, course_detail_json)
        resp = self.client.get_json(url)
        course_detail_json = json.loads(resp.content)
        self.assertEqual([], course_detail_json['pre_requisite_courses'])

    @mock.patch.dict("django.conf.settings.FEATURES", {'ENABLE_PREREQUISITE_COURSES': True, 'MILESTONES_APP': True})
    def test_invalid_pre_requisite_course(self):
        url = get_url(self.course.id)
        resp = self.client.get_json(url)
        course_detail_json = json.loads(resp.content)

        # update pre requisite courses one valid and one invalid key
        pre_requisite_course = CourseFactory.create(org='edX', course='900', run='test_run')
        pre_requisite_course_keys = [unicode(pre_requisite_course.id), 'invalid_key']
        course_detail_json['pre_requisite_courses'] = pre_requisite_course_keys
        response = self.client.ajax_post(url, course_detail_json)
        self.assertEqual(400, response.status_code)

    @ddt.data(
        (False, False, False),
        (True, False, True),
        (False, True, False),
        (True, True, True),
    )
    @override_settings(MKTG_URLS={'ROOT': 'dummy-root'})
    def test_visibility_of_entrance_exam_section(self, feature_flags):
        """
        Tests entrance exam section is available if ENTRANCE_EXAMS feature is enabled no matter any other
        feature is enabled or disabled i.e ENABLE_MKTG_SITE.
        """
        with patch.dict("django.conf.settings.FEATURES", {
            'ENTRANCE_EXAMS': feature_flags[0],
            'ENABLE_MKTG_SITE': feature_flags[1]
        }):
            course_details_url = get_url(self.course.id)
            resp = self.client.get_html(course_details_url)
            self.assertEqual(
                feature_flags[2],
                '<h3 id="heading-entrance-exam">' in resp.content
            )

    @override_settings(MKTG_URLS={'ROOT': 'dummy-root'})
    def test_marketing_site_fetch(self):
        settings_details_url = get_url(self.course.id)

        with mock.patch.dict('django.conf.settings.FEATURES', {
            'ENABLE_MKTG_SITE': True,
            'ENTRANCE_EXAMS': False,
            'ENABLE_PREREQUISITE_COURSES': False
        }):
            response = self.client.get_html(settings_details_url)
            self.assertNotContains(response, "Course Summary Page")
            self.assertNotContains(response, "Send a note to students via email")
            self.assertContains(response, "course summary page will not be viewable")

            self.assertContains(response, "Course Start Date")
            self.assertContains(response, "Course End Date")
            self.assertContains(response, "Enrollment Start Date")
            self.assertContains(response, "Enrollment End Date")
            self.assertContains(response, "not the dates shown on your course summary page")

            self.assertContains(response, "Introducing Your Course")
            self.assertContains(response, "Course Card Image")
            self.assertContains(response, "Course Short Description")
            self.assertNotContains(response, "Course Title")
            self.assertNotContains(response, "Course Subtitle")
            self.assertNotContains(response, "Course Duration")
            self.assertNotContains(response, "Course Description")
            self.assertNotContains(response, "Course Overview")
            self.assertNotContains(response, "Course Introduction Video")
            self.assertNotContains(response, "Requirements")
            self.assertNotContains(response, "Course Banner Image")
            self.assertNotContains(response, "Course Video Thumbnail Image")

    @unittest.skipUnless(settings.FEATURES.get('ENTRANCE_EXAMS', False), True)
    def test_entrance_exam_created_updated_and_deleted_successfully(self):
        settings_details_url = get_url(self.course.id)
        data = {
            'entrance_exam_enabled': 'true',
            'entrance_exam_minimum_score_pct': '60',
            'syllabus': 'none',
            'short_description': 'empty',
            'overview': '',
            'effort': '',
            'intro_video': ''
        }
        response = self.client.post(settings_details_url, data=json.dumps(data), content_type='application/json',
                                    HTTP_ACCEPT='application/json')
        self.assertEquals(response.status_code, 200)
        course = modulestore().get_course(self.course.id)
        self.assertTrue(course.entrance_exam_enabled)
        self.assertEquals(course.entrance_exam_minimum_score_pct, .60)

        # Update the entrance exam
        data['entrance_exam_enabled'] = "true"
        data['entrance_exam_minimum_score_pct'] = "80"
        response = self.client.post(
            settings_details_url,
            data=json.dumps(data),
            content_type='application/json',
            HTTP_ACCEPT='application/json'
        )
        self.assertEquals(response.status_code, 200)
        course = modulestore().get_course(self.course.id)
        self.assertTrue(course.entrance_exam_enabled)
        self.assertEquals(course.entrance_exam_minimum_score_pct, .80)

        # Delete the entrance exam
        data['entrance_exam_enabled'] = "false"
        response = self.client.post(
            settings_details_url,
            data=json.dumps(data),
            content_type='application/json',
            HTTP_ACCEPT='application/json'
        )
        course = modulestore().get_course(self.course.id)
        self.assertEquals(response.status_code, 200)
        self.assertFalse(course.entrance_exam_enabled)
        self.assertEquals(course.entrance_exam_minimum_score_pct, None)

    @unittest.skipUnless(settings.FEATURES.get('ENTRANCE_EXAMS', False), True)
    def test_entrance_exam_store_default_min_score(self):
        """
        test that creating an entrance exam should store the default value, if key missing in json request
        or entrance_exam_minimum_score_pct is an empty string
        """
        settings_details_url = get_url(self.course.id)
        test_data_1 = {
            'entrance_exam_enabled': 'true',
            'syllabus': 'none',
            'short_description': 'empty',
            'overview': '',
            'effort': '',
            'intro_video': ''
        }
        response = self.client.post(
            settings_details_url,
            data=json.dumps(test_data_1),
            content_type='application/json',
            HTTP_ACCEPT='application/json'
        )
        self.assertEquals(response.status_code, 200)
        course = modulestore().get_course(self.course.id)
        self.assertTrue(course.entrance_exam_enabled)

        # entrance_exam_minimum_score_pct is not present in the request so default value should be saved.
        self.assertEquals(course.entrance_exam_minimum_score_pct, .5)

        #add entrance_exam_minimum_score_pct with empty value in json request.
        test_data_2 = {
            'entrance_exam_enabled': 'true',
            'entrance_exam_minimum_score_pct': '',
            'syllabus': 'none',
            'short_description': 'empty',
            'overview': '',
            'effort': '',
            'intro_video': ''
        }

        response = self.client.post(
            settings_details_url,
            data=json.dumps(test_data_2),
            content_type='application/json',
            HTTP_ACCEPT='application/json'
        )
        self.assertEquals(response.status_code, 200)
        course = modulestore().get_course(self.course.id)
        self.assertTrue(course.entrance_exam_enabled)
        self.assertEquals(course.entrance_exam_minimum_score_pct, .5)

    def test_editable_short_description_fetch(self):
        settings_details_url = get_url(self.course.id)

        with mock.patch.dict('django.conf.settings.FEATURES', {'EDITABLE_SHORT_DESCRIPTION': False}):
            response = self.client.get_html(settings_details_url)
            self.assertNotContains(response, "Course Short Description")

    def test_regular_site_fetch(self):
        settings_details_url = get_url(self.course.id)

        with mock.patch.dict('django.conf.settings.FEATURES', {'ENABLE_MKTG_SITE': False,
                                                               'ENABLE_EXTENDED_COURSE_DETAILS': True}):
            response = self.client.get_html(settings_details_url)
            self.assertContains(response, "Course Summary Page")
            self.assertContains(response, "Send a note to students via email")
            self.assertNotContains(response, "course summary page will not be viewable")

            self.assertContains(response, "Course Start Date")
            self.assertContains(response, "Course End Date")
            self.assertContains(response, "Enrollment Start Date")
            self.assertContains(response, "Enrollment End Date")
            self.assertNotContains(response, "not the dates shown on your course summary page")

            self.assertContains(response, "Introducing Your Course")
            self.assertContains(response, "Course Card Image")
            self.assertContains(response, "Course Title")
            self.assertContains(response, "Course Subtitle")
            self.assertContains(response, "Course Duration")
            self.assertContains(response, "Course Description")
            self.assertContains(response, "Course Short Description")
            self.assertContains(response, "Course Overview")
            self.assertContains(response, "Course Introduction Video")
            self.assertContains(response, "Requirements")
            self.assertContains(response, "Course Banner Image")
            self.assertContains(response, "Course Video Thumbnail Image")


@ddt.ddt
class CourseGradingTest(CourseTestCase):
    """
    Tests for the course settings grading page.
    """
    def test_initial_grader(self):
        test_grader = CourseGradingModel(self.course)
        self.assertIsNotNone(test_grader.graders)
        self.assertIsNotNone(test_grader.grade_cutoffs)

    def test_fetch_grader(self):
        test_grader = CourseGradingModel.fetch(self.course.id)
        self.assertIsNotNone(test_grader.graders, "No graders")
        self.assertIsNotNone(test_grader.grade_cutoffs, "No cutoffs")

        for i, grader in enumerate(test_grader.graders):
            subgrader = CourseGradingModel.fetch_grader(self.course.id, i)
            self.assertDictEqual(grader, subgrader, str(i) + "th graders not equal")

    @ddt.data(ModuleStoreEnum.Type.mongo, ModuleStoreEnum.Type.split)
    def test_update_from_json(self, store):
        self.course = CourseFactory.create(default_store=store)

        test_grader = CourseGradingModel.fetch(self.course.id)
        altered_grader = CourseGradingModel.update_from_json(self.course.id, test_grader.__dict__, self.user)
        self.assertDictEqual(test_grader.__dict__, altered_grader.__dict__, "Noop update")

        test_grader.graders[0]['weight'] = test_grader.graders[0].get('weight') * 2
        altered_grader = CourseGradingModel.update_from_json(self.course.id, test_grader.__dict__, self.user)
        self.assertDictEqual(test_grader.__dict__, altered_grader.__dict__, "Weight[0] * 2")

        # test for bug LMS-11485
        with modulestore().bulk_operations(self.course.id):
            new_grader = test_grader.graders[0].copy()
            new_grader['type'] += '_foo'
            new_grader['short_label'] += '_foo'
            new_grader['id'] = len(test_grader.graders)
            test_grader.graders.append(new_grader)
            # don't use altered cached def, get a fresh one
            CourseGradingModel.update_from_json(self.course.id, test_grader.__dict__, self.user)
            altered_grader = CourseGradingModel.fetch(self.course.id)
            self.assertDictEqual(test_grader.__dict__, altered_grader.__dict__)

        test_grader.grade_cutoffs['D'] = 0.3
        altered_grader = CourseGradingModel.update_from_json(self.course.id, test_grader.__dict__, self.user)
        self.assertDictEqual(test_grader.__dict__, altered_grader.__dict__, "cutoff add D")

        test_grader.grace_period = {'hours': 4, 'minutes': 5, 'seconds': 0}
        altered_grader = CourseGradingModel.update_from_json(self.course.id, test_grader.__dict__, self.user)
        self.assertDictEqual(test_grader.__dict__, altered_grader.__dict__, "4 hour grace period")

    def test_update_grader_from_json(self):
        test_grader = CourseGradingModel.fetch(self.course.id)
        altered_grader = CourseGradingModel.update_grader_from_json(
            self.course.id, test_grader.graders[1], self.user
        )
        self.assertDictEqual(test_grader.graders[1], altered_grader, "Noop update")

        test_grader.graders[1]['min_count'] = test_grader.graders[1].get('min_count') + 2
        altered_grader = CourseGradingModel.update_grader_from_json(
            self.course.id, test_grader.graders[1], self.user)
        self.assertDictEqual(test_grader.graders[1], altered_grader, "min_count[1] + 2")

        test_grader.graders[1]['drop_count'] = test_grader.graders[1].get('drop_count') + 1
        altered_grader = CourseGradingModel.update_grader_from_json(
            self.course.id, test_grader.graders[1], self.user)
        self.assertDictEqual(test_grader.graders[1], altered_grader, "drop_count[1] + 2")

    def test_update_cutoffs_from_json(self):
        test_grader = CourseGradingModel.fetch(self.course.id)
        CourseGradingModel.update_cutoffs_from_json(self.course.id, test_grader.grade_cutoffs, self.user)
        # Unlike other tests, need to actually perform a db fetch for this test since update_cutoffs_from_json
        #  simply returns the cutoffs you send into it, rather than returning the db contents.
        altered_grader = CourseGradingModel.fetch(self.course.id)
        self.assertDictEqual(test_grader.grade_cutoffs, altered_grader.grade_cutoffs, "Noop update")

        test_grader.grade_cutoffs['D'] = 0.3
        CourseGradingModel.update_cutoffs_from_json(self.course.id, test_grader.grade_cutoffs, self.user)
        altered_grader = CourseGradingModel.fetch(self.course.id)
        self.assertDictEqual(test_grader.grade_cutoffs, altered_grader.grade_cutoffs, "cutoff add D")

        test_grader.grade_cutoffs['Pass'] = 0.75
        CourseGradingModel.update_cutoffs_from_json(self.course.id, test_grader.grade_cutoffs, self.user)
        altered_grader = CourseGradingModel.fetch(self.course.id)
        self.assertDictEqual(test_grader.grade_cutoffs, altered_grader.grade_cutoffs, "cutoff change 'Pass'")

    def test_delete_grace_period(self):
        test_grader = CourseGradingModel.fetch(self.course.id)
        CourseGradingModel.update_grace_period_from_json(
            self.course.id, test_grader.grace_period, self.user
        )
        # update_grace_period_from_json doesn't return anything, so query the db for its contents.
        altered_grader = CourseGradingModel.fetch(self.course.id)
        self.assertEqual(test_grader.grace_period, altered_grader.grace_period, "Noop update")

        test_grader.grace_period = {'hours': 15, 'minutes': 5, 'seconds': 30}
        CourseGradingModel.update_grace_period_from_json(
            self.course.id, test_grader.grace_period, self.user)
        altered_grader = CourseGradingModel.fetch(self.course.id)
        self.assertDictEqual(test_grader.grace_period, altered_grader.grace_period, "Adding in a grace period")

        test_grader.grace_period = {'hours': 1, 'minutes': 10, 'seconds': 0}
        # Now delete the grace period
        CourseGradingModel.delete_grace_period(self.course.id, self.user)
        # update_grace_period_from_json doesn't return anything, so query the db for its contents.
        altered_grader = CourseGradingModel.fetch(self.course.id)
        # Once deleted, the grace period should simply be None
        self.assertEqual(None, altered_grader.grace_period, "Delete grace period")

    def test_update_section_grader_type(self):
        # Get the descriptor and the section_grader_type and assert they are the default values
        descriptor = modulestore().get_item(self.course.location)
        section_grader_type = CourseGradingModel.get_section_grader_type(self.course.location)

        self.assertEqual('notgraded', section_grader_type['graderType'])
        self.assertEqual(None, descriptor.format)
        self.assertEqual(False, descriptor.graded)

        # Change the default grader type to Homework, which should also mark the section as graded
        CourseGradingModel.update_section_grader_type(self.course, 'Homework', self.user)
        descriptor = modulestore().get_item(self.course.location)
        section_grader_type = CourseGradingModel.get_section_grader_type(self.course.location)

        self.assertEqual('Homework', section_grader_type['graderType'])
        self.assertEqual('Homework', descriptor.format)
        self.assertEqual(True, descriptor.graded)

        # Change the grader type back to notgraded, which should also unmark the section as graded
        CourseGradingModel.update_section_grader_type(self.course, 'notgraded', self.user)
        descriptor = modulestore().get_item(self.course.location)
        section_grader_type = CourseGradingModel.get_section_grader_type(self.course.location)

        self.assertEqual('notgraded', section_grader_type['graderType'])
        self.assertEqual(None, descriptor.format)
        self.assertEqual(False, descriptor.graded)

    def test_get_set_grader_types_ajax(self):
        """
        Test configuring the graders via ajax calls
        """
        grader_type_url_base = get_url(self.course.id, 'grading_handler')
        # test get whole
        response = self.client.get_json(grader_type_url_base)
        whole_model = json.loads(response.content)
        self.assertIn('graders', whole_model)
        self.assertIn('grade_cutoffs', whole_model)
        self.assertIn('grace_period', whole_model)
        # test post/update whole
        whole_model['grace_period'] = {'hours': 1, 'minutes': 30, 'seconds': 0}
        response = self.client.ajax_post(grader_type_url_base, whole_model)
        self.assertEqual(200, response.status_code)
        response = self.client.get_json(grader_type_url_base)
        whole_model = json.loads(response.content)
        self.assertEqual(whole_model['grace_period'], {'hours': 1, 'minutes': 30, 'seconds': 0})
        # test get one grader
        self.assertGreater(len(whole_model['graders']), 1)  # ensure test will make sense
        response = self.client.get_json(grader_type_url_base + '/1')
        grader_sample = json.loads(response.content)
        self.assertEqual(grader_sample, whole_model['graders'][1])
        # test add grader
        new_grader = {
            "type": "Extra Credit",
            "min_count": 1,
            "drop_count": 2,
            "short_label": None,
            "weight": 15,
        }
        response = self.client.ajax_post(
            '{}/{}'.format(grader_type_url_base, len(whole_model['graders'])),
            new_grader
        )
        self.assertEqual(200, response.status_code)
        grader_sample = json.loads(response.content)
        new_grader['id'] = len(whole_model['graders'])
        self.assertEqual(new_grader, grader_sample)
        # test delete grader
        response = self.client.delete(grader_type_url_base + '/1', HTTP_ACCEPT="application/json")
        self.assertEqual(204, response.status_code)
        response = self.client.get_json(grader_type_url_base)
        updated_model = json.loads(response.content)
        new_grader['id'] -= 1  # one fewer and the id mutates
        self.assertIn(new_grader, updated_model['graders'])
        self.assertNotIn(whole_model['graders'][1], updated_model['graders'])

    def setup_test_set_get_section_grader_ajax(self):
        """
        Populate the course, grab a section, get the url for the assignment type access
        """
        self.populate_course()
        sections = modulestore().get_items(self.course.id, qualifiers={'category': "sequential"})
        # see if test makes sense
        self.assertGreater(len(sections), 0, "No sections found")
        section = sections[0]  # just take the first one
        return reverse_usage_url('xblock_handler', section.location)

    def test_set_get_section_grader_ajax(self):
        """
        Test setting and getting section grades via the grade as url
        """
        grade_type_url = self.setup_test_set_get_section_grader_ajax()
        response = self.client.ajax_post(grade_type_url, {'graderType': u'Homework'})
        self.assertEqual(200, response.status_code)
        response = self.client.get_json(grade_type_url + '?fields=graderType')
        self.assertEqual(json.loads(response.content).get('graderType'), u'Homework')
        # and unset
        response = self.client.ajax_post(grade_type_url, {'graderType': u'notgraded'})
        self.assertEqual(200, response.status_code)
        response = self.client.get_json(grade_type_url + '?fields=graderType')
        self.assertEqual(json.loads(response.content).get('graderType'), u'notgraded')


@ddt.ddt
class CourseMetadataEditingTest(CourseTestCase):
    """
    Tests for CourseMetadata.
    """
    def setUp(self):
        CourseTestCase.setUp(self)
        self.fullcourse = CourseFactory.create()
        self.course_setting_url = get_url(self.course.id, 'advanced_settings_handler')
        self.fullcourse_setting_url = get_url(self.fullcourse.id, 'advanced_settings_handler')
        self.notes_tab = {"type": "notes", "name": "My Notes"}

    def test_fetch_initial_fields(self):
        test_model = CourseMetadata.fetch(self.course)
        self.assertIn('display_name', test_model, 'Missing editable metadata field')
        self.assertEqual(test_model['display_name']['value'], self.course.display_name)

        test_model = CourseMetadata.fetch(self.fullcourse)
        self.assertNotIn('graceperiod', test_model, 'blacklisted field leaked in')
        self.assertIn('display_name', test_model, 'full missing editable metadata field')
        self.assertEqual(test_model['display_name']['value'], self.fullcourse.display_name)
        self.assertIn('rerandomize', test_model, 'Missing rerandomize metadata field')
        self.assertIn('showanswer', test_model, 'showanswer field ')
        self.assertIn('xqa_key', test_model, 'xqa_key field ')

    @patch.dict(settings.FEATURES, {'ENABLE_EXPORT_GIT': True})
    def test_fetch_giturl_present(self):
        """
        If feature flag ENABLE_EXPORT_GIT is on, show the setting as a non-deprecated Advanced Setting.
        """
        test_model = CourseMetadata.fetch(self.fullcourse)
        self.assertIn('giturl', test_model)

    @patch.dict(settings.FEATURES, {'ENABLE_EXPORT_GIT': False})
    def test_fetch_giturl_not_present(self):
        """
        If feature flag ENABLE_EXPORT_GIT is off, don't show the setting at all on the Advanced Settings page.
        """
        test_model = CourseMetadata.fetch(self.fullcourse)
        self.assertNotIn('giturl', test_model)

    @patch.dict(settings.FEATURES, {'ENABLE_EXPORT_GIT': False})
    def test_validate_update_filtered_off(self):
        """
        If feature flag is off, then giturl must be filtered.
        """
        # pylint: disable=unused-variable
        is_valid, errors, test_model = CourseMetadata.validate_and_update_from_json(
            self.course,
            {
                "giturl": {"value": "http://example.com"},
            },
            user=self.user
        )
        self.assertNotIn('giturl', test_model)

    @patch.dict(settings.FEATURES, {'ENABLE_EXPORT_GIT': True})
    def test_validate_update_filtered_on(self):
        """
        If feature flag is on, then giturl must not be filtered.
        """
        # pylint: disable=unused-variable
        is_valid, errors, test_model = CourseMetadata.validate_and_update_from_json(
            self.course,
            {
                "giturl": {"value": "http://example.com"},
            },
            user=self.user
        )
        self.assertIn('giturl', test_model)

    @patch.dict(settings.FEATURES, {'ENABLE_EXPORT_GIT': True})
    def test_update_from_json_filtered_on(self):
        """
        If feature flag is on, then giturl must be updated.
        """
        test_model = CourseMetadata.update_from_json(
            self.course,
            {
                "giturl": {"value": "http://example.com"},
            },
            user=self.user
        )
        self.assertIn('giturl', test_model)

    @patch.dict(settings.FEATURES, {'ENABLE_EXPORT_GIT': False})
    def test_update_from_json_filtered_off(self):
        """
        If feature flag is on, then giturl must not be updated.
        """
        test_model = CourseMetadata.update_from_json(
            self.course,
            {
                "giturl": {"value": "http://example.com"},
            },
            user=self.user
        )
        self.assertNotIn('giturl', test_model)

    @patch.dict(settings.FEATURES, {'ENABLE_EDXNOTES': True})
    def test_edxnotes_present(self):
        """
        If feature flag ENABLE_EDXNOTES is on, show the setting as a non-deprecated Advanced Setting.
        """
        test_model = CourseMetadata.fetch(self.fullcourse)
        self.assertIn('edxnotes', test_model)

    @patch.dict(settings.FEATURES, {'ENABLE_EDXNOTES': False})
    def test_edxnotes_not_present(self):
        """
        If feature flag ENABLE_EDXNOTES is off, don't show the setting at all on the Advanced Settings page.
        """
        test_model = CourseMetadata.fetch(self.fullcourse)
        self.assertNotIn('edxnotes', test_model)

    @patch.dict(settings.FEATURES, {'ENABLE_EDXNOTES': False})
    def test_validate_update_filtered_edxnotes_off(self):
        """
        If feature flag is off, then edxnotes must be filtered.
        """
        # pylint: disable=unused-variable
        is_valid, errors, test_model = CourseMetadata.validate_and_update_from_json(
            self.course,
            {
                "edxnotes": {"value": "true"},
            },
            user=self.user
        )
        self.assertNotIn('edxnotes', test_model)

    @patch.dict(settings.FEATURES, {'ENABLE_EDXNOTES': True})
    def test_validate_update_filtered_edxnotes_on(self):
        """
        If feature flag is on, then edxnotes must not be filtered.
        """
        # pylint: disable=unused-variable
        is_valid, errors, test_model = CourseMetadata.validate_and_update_from_json(
            self.course,
            {
                "edxnotes": {"value": "true"},
            },
            user=self.user
        )
        self.assertIn('edxnotes', test_model)

    @patch.dict(settings.FEATURES, {'ENABLE_EDXNOTES': True})
    def test_update_from_json_filtered_edxnotes_on(self):
        """
        If feature flag is on, then edxnotes must be updated.
        """
        test_model = CourseMetadata.update_from_json(
            self.course,
            {
                "edxnotes": {"value": "true"},
            },
            user=self.user
        )
        self.assertIn('edxnotes', test_model)

    @patch.dict(settings.FEATURES, {'ENABLE_EDXNOTES': False})
    def test_update_from_json_filtered_edxnotes_off(self):
        """
        If feature flag is off, then edxnotes must not be updated.
        """
        test_model = CourseMetadata.update_from_json(
            self.course,
            {
                "edxnotes": {"value": "true"},
            },
            user=self.user
        )
        self.assertNotIn('edxnotes', test_model)

    def test_allow_unsupported_xblocks(self):
        """
        allow_unsupported_xblocks is only shown in Advanced Settings if
        XBlockStudioConfigurationFlag is enabled.
        """
        self.assertNotIn('allow_unsupported_xblocks', CourseMetadata.fetch(self.fullcourse))
        XBlockStudioConfigurationFlag(enabled=True).save()
        self.assertIn('allow_unsupported_xblocks', CourseMetadata.fetch(self.fullcourse))

    def test_validate_from_json_correct_inputs(self):
        is_valid, errors, test_model = CourseMetadata.validate_and_update_from_json(
            self.course,
            {
                "advertised_start": {"value": "start A"},
                "days_early_for_beta": {"value": 2},
                "advanced_modules": {"value": ['notes']},
            },
            user=self.user
        )
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
        self.update_check(test_model)

        # Tab gets tested in test_advanced_settings_munge_tabs
        self.assertIn('advanced_modules', test_model, 'Missing advanced_modules')
        self.assertEqual(test_model['advanced_modules']['value'], ['notes'], 'advanced_module is not updated')

    def test_validate_from_json_wrong_inputs(self):
        # input incorrectly formatted data
        is_valid, errors, test_model = CourseMetadata.validate_and_update_from_json(
            self.course,
            {
                "advertised_start": {"value": 1, "display_name": "Course Advertised Start Date", },
                "days_early_for_beta": {"value": "supposed to be an integer",
                                        "display_name": "Days Early for Beta Users", },
                "advanced_modules": {"value": 1, "display_name": "Advanced Module List", },
            },
            user=self.user
        )

        # Check valid results from validate_and_update_from_json
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 3)
        self.assertFalse(test_model)

        error_keys = set([error_obj['model']['display_name'] for error_obj in errors])
        test_keys = set(['Advanced Module List', 'Course Advertised Start Date', 'Days Early for Beta Users'])
        self.assertEqual(error_keys, test_keys)

        # try fresh fetch to ensure no update happened
        fresh = modulestore().get_course(self.course.id)
        test_model = CourseMetadata.fetch(fresh)

        self.assertNotEqual(test_model['advertised_start']['value'], 1, 'advertised_start should not be updated to a wrong value')
        self.assertNotEqual(test_model['days_early_for_beta']['value'], "supposed to be an integer",
                            'days_early_for beta should not be updated to a wrong value')

    def test_correct_http_status(self):
        json_data = json.dumps({
            "advertised_start": {"value": 1, "display_name": "Course Advertised Start Date", },
            "days_early_for_beta": {
                "value": "supposed to be an integer",
                "display_name": "Days Early for Beta Users",
            },
            "advanced_modules": {"value": 1, "display_name": "Advanced Module List", },
        })
        response = self.client.ajax_post(self.course_setting_url, json_data)
        self.assertEqual(400, response.status_code)

    def test_update_from_json(self):
        test_model = CourseMetadata.update_from_json(
            self.course,
            {
                "advertised_start": {"value": "start A"},
                "days_early_for_beta": {"value": 2},
            },
            user=self.user
        )
        self.update_check(test_model)
        # try fresh fetch to ensure persistence
        fresh = modulestore().get_course(self.course.id)
        test_model = CourseMetadata.fetch(fresh)
        self.update_check(test_model)
        # now change some of the existing metadata
        test_model = CourseMetadata.update_from_json(
            fresh,
            {
                "advertised_start": {"value": "start B"},
                "display_name": {"value": "jolly roger"},
            },
            user=self.user
        )
        self.assertIn('display_name', test_model, 'Missing editable metadata field')
        self.assertEqual(test_model['display_name']['value'], 'jolly roger', "not expected value")
        self.assertIn('advertised_start', test_model, 'Missing revised advertised_start metadata field')
        self.assertEqual(test_model['advertised_start']['value'], 'start B', "advertised_start not expected value")

    def update_check(self, test_model):
        """
        checks that updates were made
        """
        self.assertIn('display_name', test_model, 'Missing editable metadata field')
        self.assertEqual(test_model['display_name']['value'], self.course.display_name)
        self.assertIn('advertised_start', test_model, 'Missing new advertised_start metadata field')
        self.assertEqual(test_model['advertised_start']['value'], 'start A', "advertised_start not expected value")
        self.assertIn('days_early_for_beta', test_model, 'Missing days_early_for_beta metadata field')
        self.assertEqual(test_model['days_early_for_beta']['value'], 2, "days_early_for_beta not expected value")

    def test_http_fetch_initial_fields(self):
        response = self.client.get_json(self.course_setting_url)
        test_model = json.loads(response.content)
        self.assertIn('display_name', test_model, 'Missing editable metadata field')
        self.assertEqual(test_model['display_name']['value'], self.course.display_name)

        response = self.client.get_json(self.fullcourse_setting_url)
        test_model = json.loads(response.content)
        self.assertNotIn('graceperiod', test_model, 'blacklisted field leaked in')
        self.assertIn('display_name', test_model, 'full missing editable metadata field')
        self.assertEqual(test_model['display_name']['value'], self.fullcourse.display_name)
        self.assertIn('rerandomize', test_model, 'Missing rerandomize metadata field')
        self.assertIn('showanswer', test_model, 'showanswer field ')
        self.assertIn('xqa_key', test_model, 'xqa_key field ')

    def test_http_update_from_json(self):
        response = self.client.ajax_post(self.course_setting_url, {
            "advertised_start": {"value": "start A"},
            "days_early_for_beta": {"value": 2},
        })
        test_model = json.loads(response.content)
        self.update_check(test_model)

        response = self.client.get_json(self.course_setting_url)
        test_model = json.loads(response.content)
        self.update_check(test_model)
        # now change some of the existing metadata
        response = self.client.ajax_post(self.course_setting_url, {
            "advertised_start": {"value": "start B"},
            "display_name": {"value": "jolly roger"}
        })
        test_model = json.loads(response.content)
        self.assertIn('display_name', test_model, 'Missing editable metadata field')
        self.assertEqual(test_model['display_name']['value'], 'jolly roger', "not expected value")
        self.assertIn('advertised_start', test_model, 'Missing revised advertised_start metadata field')
        self.assertEqual(test_model['advertised_start']['value'], 'start B', "advertised_start not expected value")

    def test_advanced_components_munge_tabs(self):
        """
        Test that adding and removing specific advanced components adds and removes tabs.
        """
        # First ensure that none of the tabs are visible
        self.assertNotIn(self.notes_tab, self.course.tabs)

        # Now enable student notes and verify that the "My Notes" tab has been added
        self.client.ajax_post(self.course_setting_url, {
            'advanced_modules': {"value": ["notes"]}
        })
        course = modulestore().get_course(self.course.id)
        self.assertIn(self.notes_tab, course.tabs)

        # Disable student notes and verify that the "My Notes" tab is gone
        self.client.ajax_post(self.course_setting_url, {
            'advanced_modules': {"value": [""]}
        })
        course = modulestore().get_course(self.course.id)
        self.assertNotIn(self.notes_tab, course.tabs)

    def test_advanced_components_munge_tabs_validation_failure(self):
        with patch('contentstore.views.course._refresh_course_tabs', side_effect=InvalidTabsException):
            resp = self.client.ajax_post(self.course_setting_url, {
                'advanced_modules': {"value": ["notes"]}
            })
            self.assertEqual(resp.status_code, 400)

            error_msg = [
                {
                    'message': 'An error occurred while trying to save your tabs',
                    'model': {'display_name': 'Tabs Exception'}
                }
            ]
            self.assertEqual(json.loads(resp.content), error_msg)

            # verify that the course wasn't saved into the modulestore
            course = modulestore().get_course(self.course.id)
            self.assertNotIn("notes", course.advanced_modules)

    @ddt.data(
        [{'type': 'course_info'}, {'type': 'courseware'}, {'type': 'wiki', 'is_hidden': True}],
        [{'type': 'course_info', 'name': 'Home'}, {'type': 'courseware', 'name': 'Course'}],
    )
    def test_course_tab_configurations(self, tab_list):
        self.course.tabs = tab_list
        modulestore().update_item(self.course, self.user.id)
        self.client.ajax_post(self.course_setting_url, {
            'advanced_modules': {"value": ["notes"]}
        })
        course = modulestore().get_course(self.course.id)
        tab_list.append(self.notes_tab)
        self.assertEqual(tab_list, course.tabs)

    @patch.dict(settings.FEATURES, {'ENABLE_EDXNOTES': True})
    @patch('xmodule.util.django.get_current_request')
    def test_post_settings_with_staff_not_enrolled(self, mock_request):
        """
        Tests that we can post advance settings when course staff is not enrolled.
        """
        mock_request.return_value = Mock(META={'HTTP_HOST': 'localhost'})
        user = UserFactory.create(is_staff=True)
        CourseStaffRole(self.course.id).add_users(user)

        client = AjaxEnabledTestClient()
        client.login(username=user.username, password=user.password)
        response = self.client.ajax_post(self.course_setting_url, {
            'advanced_modules': {"value": [""]}
        })
        self.assertEqual(response.status_code, 200)


class CourseGraderUpdatesTest(CourseTestCase):
    """
    Test getting, deleting, adding, & updating graders
    """
    def setUp(self):
        """Compute the url to use in tests"""
        super(CourseGraderUpdatesTest, self).setUp()
        self.url = get_url(self.course.id, 'grading_handler')
        self.starting_graders = CourseGradingModel(self.course).graders

    def test_get(self):
        """Test getting a specific grading type record."""
        resp = self.client.get_json(self.url + '/0')
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(self.starting_graders[0], obj)

    def test_delete(self):
        """Test deleting a specific grading type record."""
        resp = self.client.delete(self.url + '/0', HTTP_ACCEPT="application/json")
        self.assertEqual(resp.status_code, 204)
        current_graders = CourseGradingModel.fetch(self.course.id).graders
        self.assertNotIn(self.starting_graders[0], current_graders)
        self.assertEqual(len(self.starting_graders) - 1, len(current_graders))

    def test_update(self):
        """Test updating a specific grading type record."""
        grader = {
            "id": 0,
            "type": "manual",
            "min_count": 5,
            "drop_count": 10,
            "short_label": "yo momma",
            "weight": 17.3,
        }
        resp = self.client.ajax_post(self.url + '/0', grader)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj, grader)
        current_graders = CourseGradingModel.fetch(self.course.id).graders
        self.assertEqual(len(self.starting_graders), len(current_graders))

    def test_add(self):
        """Test adding a grading type record."""
        # the same url works for changing the whole grading model (graceperiod, cutoffs, and grading types) when
        # the grading_index is None; thus, using None to imply adding a grading_type doesn't work; so, it uses an
        # index out of bounds to imply create item.
        grader = {
            "type": "manual",
            "min_count": 5,
            "drop_count": 10,
            "short_label": "yo momma",
            "weight": 17.3,
        }
        resp = self.client.ajax_post('{}/{}'.format(self.url, len(self.starting_graders) + 1), grader)
        self.assertEqual(resp.status_code, 200)
        obj = json.loads(resp.content)
        self.assertEqual(obj['id'], len(self.starting_graders))
        del obj['id']
        self.assertEqual(obj, grader)
        current_graders = CourseGradingModel.fetch(self.course.id).graders
        self.assertEqual(len(self.starting_graders) + 1, len(current_graders))


class CourseEnrollmentEndFieldTest(CourseTestCase):
    """
    Base class to test the enrollment end fields in the course settings details view in Studio
    when using marketing site flag and global vs non-global staff to access the page.
    """
    NOT_EDITABLE_HELPER_MESSAGE = "Contact your edX Partner Manager to update these settings."
    NOT_EDITABLE_DATE_WRAPPER = "<div class=\"field date is-not-editable\" id=\"field-enrollment-end-date\">"
    NOT_EDITABLE_TIME_WRAPPER = "<div class=\"field time is-not-editable\" id=\"field-enrollment-end-time\">"
    NOT_EDITABLE_DATE_FIELD = "<input type=\"text\" class=\"end-date date end\" \
id=\"course-enrollment-end-date\" placeholder=\"MM/DD/YYYY\" autocomplete=\"off\" readonly aria-readonly=\"true\" />"
    NOT_EDITABLE_TIME_FIELD = "<input type=\"text\" class=\"time end\" id=\"course-enrollment-end-time\" \
value=\"\" placeholder=\"HH:MM\" autocomplete=\"off\" readonly aria-readonly=\"true\" />"

    EDITABLE_DATE_WRAPPER = "<div class=\"field date \" id=\"field-enrollment-end-date\">"
    EDITABLE_TIME_WRAPPER = "<div class=\"field time \" id=\"field-enrollment-end-time\">"
    EDITABLE_DATE_FIELD = "<input type=\"text\" class=\"end-date date end\" \
id=\"course-enrollment-end-date\" placeholder=\"MM/DD/YYYY\" autocomplete=\"off\"  />"
    EDITABLE_TIME_FIELD = "<input type=\"text\" class=\"time end\" \
id=\"course-enrollment-end-time\" value=\"\" placeholder=\"HH:MM\" autocomplete=\"off\"  />"

    EDITABLE_ELEMENTS = [
        EDITABLE_DATE_WRAPPER,
        EDITABLE_TIME_WRAPPER,
        EDITABLE_DATE_FIELD,
        EDITABLE_TIME_FIELD,
    ]

    NOT_EDITABLE_ELEMENTS = [
        NOT_EDITABLE_HELPER_MESSAGE,
        NOT_EDITABLE_DATE_WRAPPER,
        NOT_EDITABLE_TIME_WRAPPER,
        NOT_EDITABLE_DATE_FIELD,
        NOT_EDITABLE_TIME_FIELD,
    ]

    def setUp(self):
        """ Initialize course used to test enrollment fields. """
        super(CourseEnrollmentEndFieldTest, self).setUp()
        self.course = CourseFactory.create(org='edX', number='dummy', display_name='Marketing Site Course')
        self.course_details_url = reverse_course_url('settings_handler', unicode(self.course.id))

    def _get_course_details_response(self, global_staff):
        """ Return the course details page as either global or non-global staff"""
        user = UserFactory(is_staff=global_staff)
        CourseInstructorRole(self.course.id).add_users(user)

        self.client.login(username=user.username, password='test')

        return self.client.get_html(self.course_details_url)

    def _verify_editable(self, response):
        """ Verify that the response has expected editable fields.

        Assert that all editable field content exists and no
        uneditable field content exists for enrollment end fields.
        """
        self.assertEqual(response.status_code, 200)
        for element in self.NOT_EDITABLE_ELEMENTS:
            self.assertNotContains(response, element)

        for element in self.EDITABLE_ELEMENTS:
            self.assertContains(response, element)

    def _verify_not_editable(self, response):
        """ Verify that the response has expected non-editable fields.

        Assert that all uneditable field content exists and no
        editable field content exists for enrollment end fields.
        """
        self.assertEqual(response.status_code, 200)
        for element in self.NOT_EDITABLE_ELEMENTS:
            self.assertContains(response, element)

        for element in self.EDITABLE_ELEMENTS:
            self.assertNotContains(response, element)

    @mock.patch.dict("django.conf.settings.FEATURES", {'ENABLE_MKTG_SITE': False})
    def test_course_details_with_disabled_setting_global_staff(self):
        """ Test that user enrollment end date is editable in response.

        Feature flag 'ENABLE_MKTG_SITE' is not enabled.
        User is global staff.
        """
        self._verify_editable(self._get_course_details_response(True))

    @mock.patch.dict("django.conf.settings.FEATURES", {'ENABLE_MKTG_SITE': False})
    def test_course_details_with_disabled_setting_non_global_staff(self):
        """ Test that user enrollment end date is editable in response.

        Feature flag 'ENABLE_MKTG_SITE' is not enabled.
        User is non-global staff.
        """
        self._verify_editable(self._get_course_details_response(False))

    @mock.patch.dict("django.conf.settings.FEATURES", {'ENABLE_MKTG_SITE': True})
    @override_settings(MKTG_URLS={'ROOT': 'dummy-root'})
    def test_course_details_with_enabled_setting_global_staff(self):
        """ Test that user enrollment end date is editable in response.

        Feature flag 'ENABLE_MKTG_SITE' is enabled.
        User is global staff.
        """
        self._verify_editable(self._get_course_details_response(True))

    @mock.patch.dict("django.conf.settings.FEATURES", {'ENABLE_MKTG_SITE': True})
    @override_settings(MKTG_URLS={'ROOT': 'dummy-root'})
    def test_course_details_with_enabled_setting_non_global_staff(self):
        """ Test that user enrollment end date is not editable in response.

        Feature flag 'ENABLE_MKTG_SITE' is enabled.
        User is non-global staff.
        """
        self._verify_not_editable(self._get_course_details_response(False))
