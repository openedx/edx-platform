from datetime import datetime, timedelta

import ddt
import factory
import mock
from django.db.models import signals
from django.test import RequestFactory

from common.lib.nodebb_client.categories import ForumCategory
from custom_settings.models import CustomSettings
from custom_settings.signals.handlers import initialize_course_settings
from lms.djangoapps.onboarding.tests.factories import UserFactory
from lms.djangoapps.student_dashboard.views import (
    get_enrolled_past_courses,
    get_joined_communities,
    get_recommended_xmodule_courses
)
from openedx.core.djangoapps.content.course_overviews.tests.factories import CourseOverviewFactory
from openedx.features.partners.tests.factories import CourseCardFactory
from student.models import CourseEnrollment
from student.tests.factories import CourseEnrollmentFactory
from xmodule.modulestore.tests.django_utils import SharedModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
class TestStudentDashboard(SharedModuleStoreTestCase):
    """
    This class is containing tests for :func:`~lms.djangpoapps.student_dashboard.views`
    """
    course_overview_kwargs = dict(
        enrollment_start=datetime.utcnow() - timedelta(days=2),
        enrollment_end=datetime.utcnow() + timedelta(days=2),
    )
    interests = ['interest_strategy_planning', 'interest_leadership_governance', 'interest_program_design']
    orphan_course_overview = course_overview = orphan_course = orphan_course_card = course_card = orphan_course = None

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def setUp(self):
        self.user = UserFactory()
        self.request = RequestFactory()
        self.request.user = self.user
        self.course = CourseFactory.create()

        user_enrollment_dict = dict(user=self.user, course_id=self.course.id, is_active=True,
                                    course__start=datetime.utcnow() - timedelta(days=2),
                                    course__end=datetime.utcnow() + timedelta(days=2))

        self.course_enrollments = [
            CourseEnrollmentFactory.create(**user_enrollment_dict)]

    @factory.django.mute_signals(signals.pre_save, signals.post_save)
    def initialize_test(self, set_interests=True, add_settings=True, initialize=True, add_course_overviews=True):
        """
        This method is for initialization of test data.
        """
        if set_interests:
            self.user.extended_profile.interests = TestStudentDashboard.interests
            self.user.extended_profile.save()  # pylint: disable=no-member

        if add_course_overviews:
            self.course_card = CourseCardFactory(course_id=self.course.id, course_name=self.course.name)
            self.course_overview = CourseOverviewFactory(display_name='test_overview',
                                                         **TestStudentDashboard.course_overview_kwargs)

            self.orphan_course = CourseFactory.create()
            self.orphan_course_overview = CourseOverviewFactory(display_name='orphan_test_overview',
                                                                id=self.orphan_course.id,
                                                                **TestStudentDashboard.course_overview_kwargs)
            self.orphan_course_card = CourseCardFactory(course_id=self.orphan_course.id,
                                                        course_name=self.orphan_course.name)
        if initialize:
            initialize_course_settings(self.course, self.course_overview, True)
            initialize_course_settings(self.orphan_course, self.orphan_course_overview, True)

        if add_settings:
            _settings, _created = CustomSettings.objects.get_or_create(id=self.course.id)
            _orphan_settings, _orphan_created = CustomSettings.objects.get_or_create(id=self.orphan_course.id)

            _settings.tags = \
                _orphan_settings.tags = 'Strategy and planning|Leadership and governance|Program design and development'

            _settings.save()
            _orphan_settings.save()

    @ddt.data(200, 500)
    def test_get_joined_communities(self, status):
        """
        This method is test method is covering :func:`~lms.djangoapps.student_dashboard.views.get_joined_communities`.
        it's result is mostly depending on mocked values and it will assert if get_joined_communities will return
        unexpected values.
        """
        with mock.patch.object(ForumCategory, 'joined') as joined:
            # Mocking NodeBB categories which an instance of `ForumCategory`
            joined.return_value = status, []
            communities = get_joined_communities('some-username')
            self.assertEqual(communities, [])

    @ddt.data('onboarding', 'other')
    def test_get_recommended_xmodule_courses(self, _from):
        """
        This method is covering :func:`~lms.djangoapps.student_dashboard.views.get_recommended_xmodule_courses`
        this test will assert if get_recommended_xmodule_courses will return any recommended course because we haven't
        set any user interests or course tags and we are expecting empty list in response.
        """
        recommended_courses = get_recommended_xmodule_courses(self.request, _from)
        self.assertEqual(len(recommended_courses), 0)

    @ddt.data('onboarding', 'other')
    def test_get_recommended_xmodule_courses_with_tags(self, _from):
        """
        This method is covering :func:`~lms.djangoapps.student_dashboard.views.get_recommended_xmodule_courses`
        without course setting tags.
        """
        self.initialize_test()

        recommended_courses = get_recommended_xmodule_courses(self.request, _from)
        self.assertion_for_test_get_recommended_xmodule_courses_with_tags(_from, recommended_courses)

    def assertion_for_test_get_recommended_xmodule_courses_with_tags(self, _from,
                                                                     recommended_courses):
        """
        This method is performing assertions on the bases of value of _form parameter for tests
        test_get_recommended_xmodule_courses_with_tags. Assertions are applied on interests,start,short_description
        properties it is also testing if it is recommending any course if _from is not onboarding.
        """
        if _from == 'onboarding':
            course_interests = 'Program design and development/ Leadership and governance/ Strategy and planning'
            self.assertEqual(recommended_courses[0].interests, course_interests)
            self.assertEqual(recommended_courses[0].start, None)
            self.assertEqual(recommended_courses[0].short_description, None)
        else:
            self.assertEqual(len(recommended_courses), 1)

    @ddt.data('onboarding', 'other')
    def test_get_recommended_xmodule_courses_without_interests(self, _from):
        """
        This method is covering :func:`~lms.djangoapps.student_dashboard.views.get_recommended_xmodule_courses` without
        settings user interests and we are expecting not recommended course in response so this test will assert if
        recommended_courses is not empty.
        """
        self.initialize_test(set_interests=False)

        recommended_courses = get_recommended_xmodule_courses(self.request, _from)
        self.assertEqual(len(recommended_courses), 0)

    @ddt.data('onboarding', 'other')
    def test_get_recommended_xmodule_courses_without_settings(self, _from):
        """
        This method is covering :func:`~lms.djangoapps.student_dashboard.views.get_recommended_xmodule_courses` without
        settings which contain course tags so thats why we are expecting empty list in recommended courses. Test will
        assert if recommended course list is not empty.
        """
        self.initialize_test(add_settings=False)

        recommended_courses = get_recommended_xmodule_courses(self.request, _from)
        self.assertEqual(len(recommended_courses), 0)

    @ddt.data('onboarding', 'other')
    def test_get_recommended_xmodule_courses_without_course_overview(self, _from):
        """
        This method is covering :func:`~lms.djangoapps.student_dashboard.views.get_recommended_xmodule_courses` without
        course overview record. As per the already implemented criteria to add the course as recommended there should
        be a valid course overview record in the database.
        """
        self.initialize_test(add_course_overviews=False, initialize=False, add_settings=False)

        recommended_courses = get_recommended_xmodule_courses(self.request, _from)
        self.assertEqual(len(recommended_courses), 0)
