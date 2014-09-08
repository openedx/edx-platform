import json

from django.test.client import RequestFactory
from django.test.utils import override_settings
from factory import post_generation, Sequence
from factory.django import DjangoModelFactory
from course_groups.tests.helpers import config_course_cohorts
from collections import namedtuple

from django.http import Http404
from django.contrib.auth.models import User
from course_groups.models import CourseUserGroup
from courseware.tests.tests import TEST_DATA_MIXED_MODULESTORE
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from course_groups.views import list_cohorts, add_cohort, users_in_cohort, add_users_to_cohort, remove_user_from_cohort

class CohortFactory(DjangoModelFactory):
    FACTORY_FOR = CourseUserGroup

    name = Sequence("cohort{}".format)
    course_id = "dummy_id"
    group_type = CourseUserGroup.COHORT

    @post_generation
    def users(self, create, extracted, **kwargs):  # pylint: disable=W0613
        self.users.add(*extracted)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class CohortViewsTestCase(ModuleStoreTestCase):
    """
    Base class which sets up a course and staff/non-staff users.
    """
    def setUp(self):
        self.course = CourseFactory.create()
        self.staff_user = UserFactory.create(is_staff=True, username="staff")
        self.non_staff_user = UserFactory.create(username="nonstaff")

    def _enroll_users(self, users, course_key):
        """Enroll each user in the specified course"""
        for user in users:
            CourseEnrollment.enroll(user, course_key)

    def _create_cohorts(self):
        """Creates cohorts for testing"""
        self.cohort1_users = [UserFactory.create() for _ in range(3)]
        self.cohort2_users = [UserFactory.create() for _ in range(2)]
        self.cohort3_users = [UserFactory.create() for _ in range(2)]
        self.cohortless_users = [UserFactory.create() for _ in range(3)]
        self.unenrolled_users = [UserFactory.create() for _ in range(3)]
        self._enroll_users(
            self.cohort1_users + self.cohort2_users + self.cohort3_users + self.cohortless_users,
            self.course.id
        )
        self.cohort1 = CohortFactory.create(course_id=self.course.id, users=self.cohort1_users)
        self.cohort2 = CohortFactory.create(course_id=self.course.id, users=self.cohort2_users)
        self.cohort3 = CohortFactory.create(course_id=self.course.id, users=self.cohort3_users)

    def _cohort_in_course(self, cohort_name, course):
        """
        Returns true iff `course` contains a cohort with the name
        `cohort_name`.
        """
        try:
            CourseUserGroup.objects.get(
                course_id=course.id,
                group_type=CourseUserGroup.COHORT,
                name=cohort_name
            )
        except CourseUserGroup.DoesNotExist:
            return False
        else:
            return True

    def _user_in_cohort(self, username, cohort):
        """
        Return true iff a user with `username` exists in `cohort`.
        """
        return username in [user.username for user in cohort.users.all()]

    def _verify_non_staff_cannot_access(self, view, request_method, view_args):
        """
        Verify that a non-staff user cannot access a given view.

        `view` is the view to test.
        `view_args` is a list of arguments (not including the request) to pass
            to the view.
        """
        if request_method == "GET":
            request = RequestFactory().get("dummy_url")
        elif request_method == "POST":
            request = RequestFactory().post("dummy_url")
        else:
            request = RequestFactory().request()
        request.user = self.non_staff_user
        view_args.insert(0, request)
        self.assertRaises(Http404, view, *view_args)


class ListCohortsTestCase(CohortViewsTestCase):
    """
    Tests the `list_cohorts` view.
    """
    def request_list_cohorts(self, course):
        """
        Call `list_cohorts` for a given `course` and return its response as a
        dict.
        """
        request = RequestFactory().get("dummy_url")
        request.user = self.staff_user
        response = list_cohorts(request, course.id.to_deprecated_string())
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)

    def verify_lists_expected_cohorts(self, response_dict, expected_cohorts):
        """
        Verify that the server response contains the expected_cohorts.
        """
        self.assertTrue(response_dict.get("success"))
        self.assertItemsEqual(
            response_dict.get("cohorts"),
            [
                {"name": cohort.name, "id": cohort.id, "user_count": cohort.user_count}
                for cohort in expected_cohorts
            ]
        )

    @staticmethod
    def create_expected_cohort(cohort, user_count):
        """
        Create a tuple storing the expected cohort information.
        """
        cohort_tuple = namedtuple("Cohort", "name id user_count")
        return cohort_tuple(name=cohort.name, id=cohort.id, user_count=user_count)

    def test_non_staff(self):
        """
        Verify that we cannot access list_cohorts if we're a non-staff user.
        """
        self._verify_non_staff_cannot_access(list_cohorts, "GET", [self.course.id.to_deprecated_string()])

    def test_no_cohorts(self):
        """
        Verify that no cohorts are in response for a course with no cohorts.
        """
        self.verify_lists_expected_cohorts(self.request_list_cohorts(self.course), [])

    def test_some_cohorts(self):
        """
        Verify that cohorts are in response for a course with some cohorts.
        """
        self._create_cohorts()
        expected_cohorts = [
            ListCohortsTestCase.create_expected_cohort(self.cohort1, 3),
            ListCohortsTestCase.create_expected_cohort(self.cohort2, 2),
            ListCohortsTestCase.create_expected_cohort(self.cohort3, 2),
        ]
        self.verify_lists_expected_cohorts(self.request_list_cohorts(self.course), expected_cohorts)

    def test_auto_cohorts(self):
        """
        Verify that auto cohorts are included in the response.
        """
        config_course_cohorts(self.course, [], cohorted=True, auto_cohort=True,
                              auto_cohort_groups=["AutoGroup1", "AutoGroup2"])

        # Will create cohort1, cohort2, and cohort3. Auto cohorts remain uncreated.
        self._create_cohorts()
        # Get the cohorts from the course, which will cause auto cohorts to be created.
        actual_cohorts = self.request_list_cohorts(self.course)
        # Get references to the created auto cohorts.
        auto_cohort_1 = CourseUserGroup.objects.get(
            course_id=self.course.location.course_key,
            group_type=CourseUserGroup.COHORT,
            name="AutoGroup1"
        )
        auto_cohort_2 = CourseUserGroup.objects.get(
            course_id=self.course.location.course_key,
            group_type=CourseUserGroup.COHORT,
            name="AutoGroup2"
        )
        expected_cohorts = [
            ListCohortsTestCase.create_expected_cohort(self.cohort1, 3),
            ListCohortsTestCase.create_expected_cohort(self.cohort2, 2),
            ListCohortsTestCase.create_expected_cohort(self.cohort3, 2),
            ListCohortsTestCase.create_expected_cohort(auto_cohort_1, 0),
            ListCohortsTestCase.create_expected_cohort(auto_cohort_2, 0),
        ]
        self.verify_lists_expected_cohorts(actual_cohorts, expected_cohorts)


class AddCohortTestCase(CohortViewsTestCase):
    """
    Tests the `add_cohort` view.
    """
    def request_add_cohort(self, cohort_name, course):
        """
        Call `add_cohort` and return its response as a dict.
        """
        request = RequestFactory().post("dummy_url", {"name": cohort_name})
        request.user = self.staff_user
        response = add_cohort(request, course.id.to_deprecated_string())
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)

    def verify_contains_added_cohort(self, response_dict, cohort_name, course, expected_error_msg=None):
        """
        Check that `add_cohort`'s response correctly returns the newly added
        cohort (or error) in the response.  Also verify that the cohort was
        actually created/exists.
        """
        if expected_error_msg is not None:
            self.assertFalse(response_dict.get("success"))
            self.assertEqual(
                response_dict.get("msg"),
                expected_error_msg
            )
        else:
            self.assertTrue(response_dict.get("success"))
            self.assertEqual(
                response_dict.get("cohort").get("name"),
                cohort_name
            )
        self.assertTrue(self._cohort_in_course(cohort_name, course))

    def test_non_staff(self):
        """
        Verify that non-staff users cannot access add_cohort.
        """
        self._verify_non_staff_cannot_access(add_cohort, "POST", [self.course.id.to_deprecated_string()])

    def test_new_cohort(self):
        """
        Verify that we can add a new cohort.
        """
        cohort_name = "New Cohort"
        self.verify_contains_added_cohort(
            self.request_add_cohort(cohort_name, self.course),
            cohort_name,
            self.course
        )

    def test_no_cohort(self):
        """
        Verify that we cannot explicitly add no cohort.
        """
        response_dict = self.request_add_cohort("", self.course)
        self.assertFalse(response_dict.get("success"))
        self.assertEqual(response_dict.get("msg"), "No name specified")

    def test_existing_cohort(self):
        """
        Verify that we cannot add a cohort with the same name as an existing
        cohort.
        """
        self._create_cohorts()
        cohort_name = self.cohort1.name
        self.verify_contains_added_cohort(
            self.request_add_cohort(cohort_name, self.course),
            cohort_name,
            self.course,
            expected_error_msg="Can't create two cohorts with the same name"
        )


class UsersInCohortTestCase(CohortViewsTestCase):
    """
    Tests the `users_in_cohort` view.
    """
    def request_users_in_cohort(self, cohort, course, requested_page, should_return_bad_request=False):
        """
        Call `users_in_cohort` for a given cohort/requested page, and return
        its response as a dict.  When `should_return_bad_request` is True,
        verify that the response indicates a bad request.
        """
        request = RequestFactory().get("dummy_url", {"page": requested_page})
        request.user = self.staff_user
        response = users_in_cohort(request, course.id.to_deprecated_string(), cohort.id)

        if should_return_bad_request:
            self.assertEqual(response.status_code, 400)
            return

        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)

    def verify_users_in_cohort_and_response(self, cohort, response_dict, expected_users, expected_page,
                                            expected_num_pages):
        """
        Check that the `users_in_cohort` response contains the expected list of
        users, page number, and total number of pages for a given cohort.  Also
        verify that those users are actually in the given cohort.
        """
        self.assertTrue(response_dict.get("success"))
        self.assertEqual(response_dict.get("page"), expected_page)
        self.assertEqual(response_dict.get("num_pages"), expected_num_pages)

        returned_users = User.objects.filter(username__in=[user.get("username") for user in response_dict.get("users")])
        self.assertItemsEqual(returned_users, expected_users)
        self.assertTrue(set(returned_users).issubset(cohort.users.all()))

    def test_non_staff(self):
        """
        Verify that non-staff users cannot access `check_users_in_cohort`.
        """
        cohort = CohortFactory.create(course_id=self.course.id, users=[])
        self._verify_non_staff_cannot_access(users_in_cohort, "GET", [self.course.id.to_deprecated_string(), cohort.id])

    def test_no_users(self):
        """
        Verify that we don't get back any users for a cohort with no users.
        """
        cohort = CohortFactory.create(course_id=self.course.id, users=[])
        response_dict = self.request_users_in_cohort(cohort, self.course, 1)
        self.verify_users_in_cohort_and_response(
            cohort,
            response_dict,
            expected_users=[],
            expected_page=1,
            expected_num_pages=1
        )

    def test_few_users(self):
        """
        Verify that we get back all users for a cohort when the cohort has
        <=100 users.
        """
        users = [UserFactory.create() for _ in range(5)]
        cohort = CohortFactory.create(course_id=self.course.id, users=users)
        response_dict = self.request_users_in_cohort(cohort, self.course, 1)
        self.verify_users_in_cohort_and_response(
            cohort,
            response_dict,
            expected_users=users,
            expected_page=1,
            expected_num_pages=1
        )

    def test_many_users(self):
        """
        Verify that pagination works correctly for cohorts with >100 users.
        """
        users = [UserFactory.create() for _ in range(101)]
        cohort = CohortFactory.create(course_id=self.course.id, users=users)
        response_dict_1 = self.request_users_in_cohort(cohort, self.course, 1)
        response_dict_2 = self.request_users_in_cohort(cohort, self.course, 2)
        self.verify_users_in_cohort_and_response(
            cohort,
            response_dict_1,
            expected_users=users[:100],
            expected_page=1,
            expected_num_pages=2
        )
        self.verify_users_in_cohort_and_response(
            cohort,
            response_dict_2,
            expected_users=users[100:],
            expected_page=2,
            expected_num_pages=2
        )

    def test_out_of_range(self):
        """
        Verify that we get a blank page of users when requesting page 0 or a
        page greater than the actual number of pages.
        """
        users = [UserFactory.create() for _ in range(5)]
        cohort = CohortFactory.create(course_id=self.course.id, users=users)
        response = self.request_users_in_cohort(cohort, self.course, 0)
        self.verify_users_in_cohort_and_response(
            cohort,
            response,
            expected_users=[],
            expected_page=0,
            expected_num_pages=1
        )
        response = self.request_users_in_cohort(cohort, self.course, 2)
        self.verify_users_in_cohort_and_response(
            cohort,
            response,
            expected_users=[],
            expected_page=2,
            expected_num_pages=1
        )

    def test_non_positive_page(self):
        """
        Verify that we get a `HttpResponseBadRequest` (bad request) when the
        page we request isn't a positive integer.
        """
        users = [UserFactory.create() for _ in range(5)]
        cohort = CohortFactory.create(course_id=self.course.id, users=users)
        self.request_users_in_cohort(cohort, self.course, "invalid", should_return_bad_request=True)
        self.request_users_in_cohort(cohort, self.course, -1, should_return_bad_request=True)


class AddUsersToCohortTestCase(CohortViewsTestCase):
    """
    Tests the `add_users_to_cohort` view.
    """
    def setUp(self):
        super(AddUsersToCohortTestCase, self).setUp()
        self._create_cohorts()

    def request_add_users_to_cohort(self, users_string, cohort, course, should_raise_404=False):
        """
        Call `add_users_to_cohort` for a given cohort, course, and list of
        users, returning its response as a dict.  When `should_raise_404` is
        True, verify that the request raised a Http404.
        """
        request = RequestFactory().post("dummy_url", {"users": users_string})
        request.user = self.staff_user
        if should_raise_404:
            self.assertRaises(
                Http404,
                lambda: add_users_to_cohort(request, course.id.to_deprecated_string(), cohort.id)
            )
        else:
            response = add_users_to_cohort(request, course.id.to_deprecated_string(), cohort.id)
            self.assertEqual(response.status_code, 200)
            return json.loads(response.content)

    def verify_added_users_to_cohort(self, response_dict, cohort, course, expected_added, expected_changed,
                                     expected_present, expected_unknown):
        """
        Check that add_users_to_cohort returned the expected response and has
        the expected side effects.

        `expected_added` is a list of users
        `expected_changed` is a list of (user, previous_cohort) tuples
        `expected_present` is a list of (user, email/username) tuples where
            email/username corresponds to the input
        `expected_unknown` is a list of strings corresponding to the input
        """
        self.assertTrue(response_dict.get("success"))
        self.assertItemsEqual(
            response_dict.get("added"),
            [
                {"username": user.username, "name": user.profile.name, "email": user.email}
                for user in expected_added
            ]
        )
        self.assertItemsEqual(
            response_dict.get("changed"),
            [
                {
                    "username": user.username,
                    "name": user.profile.name,
                    "email": user.email,
                    "previous_cohort": previous_cohort
                }
                for (user, previous_cohort) in expected_changed
            ]
        )
        self.assertItemsEqual(
            response_dict.get("present"),
            [username_or_email for (_, username_or_email) in expected_present]
        )
        self.assertItemsEqual(response_dict.get("unknown"), expected_unknown)
        for user in expected_added + [user for (user, _) in expected_changed + expected_present]:
            self.assertEqual(
                CourseUserGroup.objects.get(
                    course_id=course.id,
                    group_type=CourseUserGroup.COHORT,
                    users__id=user.id
                ),
                cohort
            )

    def test_non_staff(self):
        """
        Verify that non-staff users cannot access `check_users_in_cohort`.
        """
        cohort = CohortFactory.create(course_id=self.course.id, users=[])
        self._verify_non_staff_cannot_access(
            add_users_to_cohort,
            "POST",
            [self.course.id.to_deprecated_string(), cohort.id]
        )

    def test_empty(self):
        """
        Verify that adding an empty list of users to a cohort has no result.
        """
        response_dict = self.request_add_users_to_cohort("", self.cohort1, self.course)
        self.verify_added_users_to_cohort(
            response_dict,
            self.cohort1,
            self.course,
            expected_added=[],
            expected_changed=[],
            expected_present=[],
            expected_unknown=[]
        )

    def test_only_added(self):
        """
        Verify that we can add users to their first cohort.
        """
        response_dict = self.request_add_users_to_cohort(
            ",".join([user.username for user in self.cohortless_users]),
            self.cohort1,
            self.course
        )
        self.verify_added_users_to_cohort(
            response_dict,
            self.cohort1,
            self.course,
            expected_added=self.cohortless_users,
            expected_changed=[],
            expected_present=[],
            expected_unknown=[]
        )

    def test_only_changed(self):
        """
        Verify that we can move users to a different cohort.
        """
        response_dict = self.request_add_users_to_cohort(
            ",".join([user.username for user in self.cohort2_users + self.cohort3_users]),
            self.cohort1,
            self.course
        )
        self.verify_added_users_to_cohort(
            response_dict,
            self.cohort1,
            self.course,
            expected_added=[],
            expected_changed=(
                [(user, self.cohort2.name) for user in self.cohort2_users] +
                [(user, self.cohort3.name) for user in self.cohort3_users]
            ),
            expected_present=[],
            expected_unknown=[]
        )

    def test_only_present(self):
        """
        Verify that we can 'add' users to their current cohort.
        """
        usernames = [user.username for user in self.cohort1_users]
        response_dict = self.request_add_users_to_cohort(
            ",".join(usernames),
            self.cohort1,
            self.course
        )
        self.verify_added_users_to_cohort(
            response_dict,
            self.cohort1,
            self.course,
            expected_added=[],
            expected_changed=[],
            expected_present=[(user, user.username) for user in self.cohort1_users],
            expected_unknown=[]
        )

    def test_only_unknown(self):
        """
        Verify that non-existent users are not added.
        """
        usernames = ["unknown_user{}".format(i) for i in range(3)]
        response_dict = self.request_add_users_to_cohort(
            ",".join(usernames),
            self.cohort1,
            self.course
        )
        self.verify_added_users_to_cohort(
            response_dict,
            self.cohort1,
            self.course,
            expected_added=[],
            expected_changed=[],
            expected_present=[],
            expected_unknown=usernames
        )

    def test_all(self):
        """
        Test all adding conditions together.
        """
        unknowns = ["unknown_user{}".format(i) for i in range(3)]
        response_dict = self.request_add_users_to_cohort(
            ",".join(
                unknowns +
                [
                    user.username
                    for user in self.cohortless_users + self.cohort1_users + self.cohort2_users + self.cohort3_users
                ]
            ),
            self.cohort1,
            self.course
        )
        self.verify_added_users_to_cohort(
            response_dict,
            self.cohort1,
            self.course,
            expected_added=self.cohortless_users,
            expected_changed=(
                [(user, self.cohort2.name) for user in self.cohort2_users] +
                [(user, self.cohort3.name) for user in self.cohort3_users]
            ),
            expected_present=[(user, user.username) for user in self.cohort1_users],
            expected_unknown=unknowns
        )

    def test_emails(self):
        """
        Verify that we can use emails to identify users.
        """
        unknown = "unknown_user@example.com"
        response_dict = self.request_add_users_to_cohort(
            ",".join([
                self.cohort1_users[0].email,
                self.cohort2_users[0].email,
                self.cohortless_users[0].email,
                unknown
            ]),
            self.cohort1,
            self.course
        )
        self.verify_added_users_to_cohort(
            response_dict,
            self.cohort1,
            self.course,
            expected_added=[self.cohortless_users[0]],
            expected_changed=[(self.cohort2_users[0], self.cohort2.name)],
            expected_present=[(self.cohort1_users[0], self.cohort1_users[0].email)],
            expected_unknown=[unknown]
        )

    def test_delimiters(self):
        """
        Verify that we can use different types of whitespace to delimit
        usernames in the user string.
        """
        unknown = "unknown_user"
        response_dict = self.request_add_users_to_cohort(
            " {} {}\t{}, \r\n{}".format(
                unknown,
                self.cohort1_users[0].username,
                self.cohort2_users[0].username,
                self.cohortless_users[0].username
            ),
            self.cohort1,
            self.course
        )
        self.verify_added_users_to_cohort(
            response_dict,
            self.cohort1,
            self.course,
            expected_added=[self.cohortless_users[0]],
            expected_changed=[(self.cohort2_users[0], self.cohort2.name)],
            expected_present=[(self.cohort1_users[0], self.cohort1_users[0].username)],
            expected_unknown=[unknown]
        )

    def test_can_cohort_unenrolled_users(self):
        """
        Verify that users can be added to a cohort of a course they're not
        enrolled in.  This feature is currently used to pre-cohort users that
        are expected to enroll in a course.
        """
        unenrolled_usernames = [user.username for user in self.unenrolled_users]
        response_dict = self.request_add_users_to_cohort(
            ",".join(unenrolled_usernames),
            self.cohort1,
            self.course
        )
        self.verify_added_users_to_cohort(
            response_dict,
            self.cohort1,
            self.course,
            expected_added=self.unenrolled_users,
            expected_changed=[],
            expected_present=[],
            expected_unknown=[]
        )

    def test_non_existent_cohort(self):
        """
        Verify that an error is raised when trying to add users to a cohort
        which does not belong to the given course.
        """
        users = [UserFactory.create(username="user{0}".format(i)) for i in range(3)]
        usernames = [user.username for user in users]
        wrong_course_key = SlashSeparatedCourseKey("some", "arbitrary", "course")
        wrong_course_cohort = CohortFactory.create(name="wrong_cohort", course_id=wrong_course_key, users=[])
        self.request_add_users_to_cohort(
            ",".join(usernames),
            wrong_course_cohort,
            self.course,
            should_raise_404=True
        )


class RemoveUserFromCohortTestCase(CohortViewsTestCase):
    """
    Tests the `remove_user_from_cohort` view.
    """
    def request_remove_user_from_cohort(self, username, cohort):
        """
        Call `remove_user_from_cohort` with the given username and cohort.
        """
        if username is not None:
            request = RequestFactory().post("dummy_url", {"username": username})
        else:
            request = RequestFactory().post("dummy_url")
        request.user = self.staff_user
        response = remove_user_from_cohort(request, self.course.id.to_deprecated_string(), cohort.id)
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)

    def verify_removed_user_from_cohort(self, username, response_dict, cohort, expected_error_msg=None):
        """
        Check that `remove_user_from_cohort` properly removes a user from a
        cohort and returns appropriate success.  If the removal should fail,
        verify that the returned error message matches the expected one.
        """
        if expected_error_msg is None:
            self.assertTrue(response_dict.get("success"))
            self.assertIsNone(response_dict.get("msg"))
            self.assertFalse(self._user_in_cohort(username, cohort))
        else:
            self.assertFalse(response_dict.get("success"))
            self.assertEqual(response_dict.get("msg"), expected_error_msg)

    def test_non_staff(self):
        """
        Verify that non-staff users cannot access `check_users_in_cohort`.
        """
        cohort = CohortFactory.create(course_id=self.course.id, users=[])
        self._verify_non_staff_cannot_access(
            remove_user_from_cohort,
            "POST",
            [self.course.id.to_deprecated_string(), cohort.id]
        )

    def test_no_username_given(self):
        """
        Verify that we get an error message when omitting a username.
        """
        cohort = CohortFactory.create(course_id=self.course.id, users=[])
        response_dict = self.request_remove_user_from_cohort(None, cohort)
        self.verify_removed_user_from_cohort(
            None,
            response_dict,
            cohort,
            expected_error_msg='No username specified'
        )

    def test_user_does_not_exist(self):
        """
        Verify that we get an error message when the requested user to remove
        does not exist.
        """
        username = "bogus"
        cohort = CohortFactory.create(course_id=self.course.id, users=[])
        response_dict = self.request_remove_user_from_cohort(
            username,
            cohort
        )
        self.verify_removed_user_from_cohort(
            username,
            response_dict,
            cohort,
            expected_error_msg='No user \'{0}\''.format(username)
        )

    def test_can_remove_user_not_in_cohort(self):
        """
        Verify that we can "remove" a user from a cohort even if they are not a
        member of that cohort.
        """
        user = UserFactory.create()
        cohort = CohortFactory.create(course_id=self.course.id, users=[])
        response_dict = self.request_remove_user_from_cohort(user.username, cohort)
        self.verify_removed_user_from_cohort(user.username, response_dict, cohort)

    def test_can_remove_user_from_cohort(self):
        """
        Verify that we can remove a user from a cohort.
        """
        user = UserFactory.create()
        cohort = CohortFactory.create(course_id=self.course.id, users=[user])
        response_dict = self.request_remove_user_from_cohort(user.username, cohort)
        self.verify_removed_user_from_cohort(user.username, response_dict, cohort)
