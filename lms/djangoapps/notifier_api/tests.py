import itertools

import ddt
from django.conf import settings
from django.test.client import RequestFactory
from django.test.utils import override_settings

from django_comment_common.models import Role, Permission
from notification_prefs import NOTIFICATION_PREF_KEY
from notifier_api.views import NotifierUsersViewSet
from opaque_keys.edx.locator import CourseLocator
from student.models import CourseEnrollment
from student.tests.factories import UserFactory, CourseEnrollmentFactory
from openedx.core.djangoapps.course_groups.tests.helpers import CohortFactory
from openedx.core.djangoapps.lang_pref import LANGUAGE_KEY
from openedx.core.djangoapps.user_api.models import UserPreference
from openedx.core.djangoapps.user_api.tests.factories import UserPreferenceFactory
from util.testing import UrlResetMixin
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


@ddt.ddt
@override_settings(EDX_API_KEY="test_api_key")
class NotifierUsersViewSetTest(UrlResetMixin, ModuleStoreTestCase):
    def setUp(self):
        super(NotifierUsersViewSetTest, self).setUp()
        self.courses = []
        self.cohorts = []
        self.user = UserFactory()
        self.notification_pref = UserPreferenceFactory(
            user=self.user,
            key=NOTIFICATION_PREF_KEY,
            value="notification pref test value"
        )

        self.list_view = NotifierUsersViewSet.as_view({"get": "list"})
        self.detail_view = NotifierUsersViewSet.as_view({"get": "retrieve"})

    def _set_up_course(self, is_course_cohorted, is_user_cohorted, is_moderator):
        cohort_config = {"cohorted": True} if is_course_cohorted else {}
        course = CourseFactory(
            number=("TestCourse{}".format(len(self.courses))),
            cohort_config=cohort_config
        )
        self.courses.append(course)
        CourseEnrollmentFactory(user=self.user, course_id=course.id)
        if is_user_cohorted:
            cohort = CohortFactory.create(
                name="Test Cohort",
                course_id=course.id,
                users=[self.user]
            )
            self.cohorts.append(cohort)
        if is_moderator:
            moderator_perm, _ = Permission.objects.get_or_create(name="see_all_cohorts")
            moderator_role = Role.objects.create(name="Moderator", course_id=course.id)
            moderator_role.permissions.add(moderator_perm)
            self.user.roles.add(moderator_role)

    def _assert_basic_user_info_correct(self, user, result_user):
        self.assertEqual(result_user["id"], user.id)
        self.assertEqual(result_user["email"], user.email)
        self.assertEqual(result_user["name"], user.profile.name)

    def test_without_api_key(self):
        request = RequestFactory().get("dummy")
        for view in [self.list_view, self.detail_view]:
            response = view(request)
            self.assertEqual(response.status_code, 403)

    # Detail view tests

    def _make_detail_request(self):
        request = RequestFactory().get("dummy", HTTP_X_EDX_API_KEY=settings.EDX_API_KEY)
        return self.detail_view(
            request,
            **{NotifierUsersViewSet.lookup_field: str(self.user.id)}
        )

    def _get_detail(self):
        response = self._make_detail_request()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data.keys()),
            {"id", "email", "name", "preferences", "course_info"}
        )
        return response.data

    def test_detail_invalid_user(self):
        UserPreference.objects.all().delete()
        response = self._make_detail_request()
        self.assertEqual(response.status_code, 404)

    def test_basic_user_info(self):
        result = self._get_detail()
        self._assert_basic_user_info_correct(self.user, result)

    def test_course_info(self):
        expected_course_info = {}
        for is_course_cohorted, is_user_cohorted, is_moderator in (
                itertools.product([True, False], [True, False], [True, False])
        ):
            self._set_up_course(is_course_cohorted, is_user_cohorted, is_moderator)
            expected_course_info[unicode(self.courses[-1].id)] = {
                "cohort_id": self.cohorts[-1].id if is_user_cohorted else None,
                "see_all_cohorts": is_moderator or not is_course_cohorted
            }
        result = self._get_detail()
        self.assertEqual(result["course_info"], expected_course_info)

    def test_course_info_unenrolled(self):
        self._set_up_course(False, False, False)
        course_id = self.courses[0].id
        CourseEnrollment.unenroll(self.user, course_id)
        result = self._get_detail()
        self.assertNotIn(unicode(course_id), result["course_info"])

    def test_course_info_no_enrollments(self):
        result = self._get_detail()
        self.assertEqual(result["course_info"], {})

    def test_course_info_non_existent_course_enrollment(self):
        CourseEnrollmentFactory(
            user=self.user,
            course_id=CourseLocator(org="dummy", course="dummy", run="non_existent")
        )
        result = self._get_detail()
        self.assertEqual(result["course_info"], {})

    def test_preferences(self):
        lang_pref = UserPreferenceFactory(
            user=self.user,
            key=LANGUAGE_KEY,
            value="language pref test value"
        )
        UserPreferenceFactory(user=self.user, key="non_included_key")
        result = self._get_detail()
        self.assertEqual(
            result["preferences"],
            {
                NOTIFICATION_PREF_KEY: self.notification_pref.value,
                LANGUAGE_KEY: lang_pref.value,
            }
        )

    # List view tests

    def _make_list_request(self, page, page_size):
        request = RequestFactory().get(
            "dummy",
            {"page": page, "page_size": page_size},
            HTTP_X_EDX_API_KEY=settings.EDX_API_KEY
        )
        return self.list_view(request)

    def _get_list(self, page=1, page_size=None):
        response = self._make_list_request(page, page_size)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            set(response.data.keys()),
            {"count", "next", "previous", "results"}
        )
        return response.data["results"]

    def test_no_users(self):
        UserPreference.objects.all().delete()
        results = self._get_list()
        self.assertEqual(len(results), 0)

    def test_multiple_users(self):
        other_user = UserFactory()
        other_notification_pref = UserPreferenceFactory(
            user=other_user,
            key=NOTIFICATION_PREF_KEY,
            value="other value"
        )
        self._set_up_course(is_course_cohorted=True, is_user_cohorted=True, is_moderator=False)
        self._set_up_course(is_course_cohorted=False, is_user_cohorted=False, is_moderator=False)
        # Users have different sets of enrollments
        CourseEnrollmentFactory(user=other_user, course_id=self.courses[0].id)

        result_map = {result["id"]: result for result in self._get_list()}
        self.assertEqual(set(result_map.keys()), {self.user.id, other_user.id})
        for user in [self.user, other_user]:
            self._assert_basic_user_info_correct(user, result_map[user.id])
        self.assertEqual(
            result_map[self.user.id]["preferences"],
            {NOTIFICATION_PREF_KEY: self.notification_pref.value}
        )
        self.assertEqual(
            result_map[other_user.id]["preferences"],
            {NOTIFICATION_PREF_KEY: other_notification_pref.value}
        )
        self.assertEqual(
            result_map[self.user.id]["course_info"],
            {
                unicode(self.courses[0].id): {
                    "cohort_id": self.cohorts[0].id,
                    "see_all_cohorts": False,
                },
                unicode(self.courses[1].id): {
                    "cohort_id": None,
                    "see_all_cohorts": True,
                },
            }
        )
        self.assertEqual(
            result_map[other_user.id]["course_info"],
            {
                unicode(self.courses[0].id): {
                    "cohort_id": None,
                    "see_all_cohorts": False,
                },
            }
        )

    @ddt.data(
        3,  # Factor of num of results
        5,  # Non-factor of num of results
        12,  # Num of results
        15  # More than num of results
    )
    def test_pagination(self, page_size):
        num_users = 12
        users = [self.user]
        while len(users) < num_users:
            new_user = UserFactory()
            users.append(new_user)
            UserPreferenceFactory(user=new_user, key=NOTIFICATION_PREF_KEY)

        num_pages = (num_users - 1) / page_size + 1
        result_list = []
        for i in range(1, num_pages + 1):
            result_list.extend(self._get_list(page=i, page_size=page_size))
        result_map = {result["id"]: result for result in result_list}

        self.assertEqual(len(result_list), num_users)
        for user in users:
            self._assert_basic_user_info_correct(user, result_map[user.id])
        self.assertEqual(
            self._make_list_request(page=(num_pages + 1), page_size=page_size).status_code,
            404
        )

    def test_db_access(self):
        for _ in range(10):
            new_user = UserFactory()
            UserPreferenceFactory(user=new_user, key=NOTIFICATION_PREF_KEY)

        # The number of queries is one for the users plus one for each prefetch
        # in NotifierUsersViewSet (roles__permissions does one for each table).
        with self.assertNumQueries(6):
            self._get_list()
