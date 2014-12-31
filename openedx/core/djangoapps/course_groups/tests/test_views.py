"""
Tests for course group views
"""
from collections import namedtuple
import json

from collections import namedtuple
from django.contrib.auth.models import User
from django.http import Http404
from django.test.client import RequestFactory
from django.test.utils import override_settings

from xmodule.modulestore.tests.django_utils import TEST_DATA_MOCK_MODULESTORE
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory
from xmodule.modulestore.django import modulestore
from opaque_keys.edx.locations import SlashSeparatedCourseKey

from ..models import CourseUserGroup
from ..views import (
    cohort_handler, users_in_cohort, add_users_to_cohort, remove_user_from_cohort, link_cohort_to_partition_group
)
from ..cohorts import (
    get_cohort, CohortAssignmentType, get_cohort_by_name, get_cohort_by_id,
    DEFAULT_COHORT_NAME, get_group_info_for_cohort
)
from .helpers import config_course_cohorts, CohortFactory


@override_settings(MODULESTORE=TEST_DATA_MOCK_MODULESTORE)
class CohortViewsTestCase(ModuleStoreTestCase):
    """
    Base class which sets up a course and staff/non-staff users.
    """
    def setUp(self):
        self.course = CourseFactory.create()
        self.staff_user = UserFactory(is_staff=True, username="staff")
        self.non_staff_user = UserFactory(username="nonstaff")

    def _enroll_users(self, users, course_key):
        """Enroll each user in the specified course"""
        for user in users:
            CourseEnrollment.enroll(user, course_key)

    def _create_cohorts(self):
        """Creates cohorts for testing"""
        self.cohort1_users = [UserFactory() for _ in range(3)]
        self.cohort2_users = [UserFactory() for _ in range(2)]
        self.cohort3_users = [UserFactory() for _ in range(2)]
        self.cohortless_users = [UserFactory() for _ in range(3)]
        self.unenrolled_users = [UserFactory() for _ in range(3)]
        self._enroll_users(
            self.cohort1_users + self.cohort2_users + self.cohort3_users + self.cohortless_users,
            self.course.id
        )
        self.cohort1 = CohortFactory(course_id=self.course.id, users=self.cohort1_users)
        self.cohort2 = CohortFactory(course_id=self.course.id, users=self.cohort2_users)
        self.cohort3 = CohortFactory(course_id=self.course.id, users=self.cohort3_users)

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


class CohortHandlerTestCase(CohortViewsTestCase):
    """
    Tests the `cohort_handler` view.
    """
    def get_cohort_handler(self, course, cohort=None):
        """
        Call a GET on `cohort_handler` for a given `course` and return its response as a
        dict. If `cohort` is specified, only information for that specific cohort is returned.
        """
        request = RequestFactory().get("dummy_url")
        request.user = self.staff_user
        if cohort:
            response = cohort_handler(request, unicode(course.id), cohort.id)
        else:
            response = cohort_handler(request, unicode(course.id))
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)

    def put_cohort_handler(self, course, cohort=None, data=None, expected_response_code=200):
        """
        Call a PUT on `cohort_handler` for a given `course` and return its response as a
        dict. If `cohort` is not specified, a new cohort is created. If `cohort` is specified,
        the existing cohort is updated.
        """
        if not isinstance(data, basestring):
            data = json.dumps(data or {})
        request = RequestFactory().put(path="dummy path", data=data, content_type="application/json")
        request.user = self.staff_user
        if cohort:
            response = cohort_handler(request, unicode(course.id), cohort.id)
        else:
            response = cohort_handler(request, unicode(course.id))
        self.assertEqual(response.status_code, expected_response_code)
        return json.loads(response.content)

    def verify_lists_expected_cohorts(self, expected_cohorts, response_dict=None):
        """
        Verify that the server response contains the expected_cohorts.
        If response_dict is None, the list of cohorts is requested from the server.
        """
        if response_dict is None:
            response_dict = self.get_cohort_handler(self.course)

        self.assertEqual(
            response_dict.get("cohorts"),
            [
                {
                    "name": cohort.name,
                    "id": cohort.id,
                    "user_count": cohort.user_count,
                    "assignment_type": cohort.assignment_type,
                    "user_partition_id": None,
                    "group_id": None
                }
                for cohort in expected_cohorts
            ]
        )

    @staticmethod
    def create_expected_cohort(cohort, user_count, assignment_type, user_partition_id=None, group_id=None):
        """
        Create a tuple storing the expected cohort information.
        """
        cohort_tuple = namedtuple("Cohort", "name id user_count assignment_type user_partition_id group_id")
        return cohort_tuple(
            name=cohort.name, id=cohort.id, user_count=user_count, assignment_type=assignment_type,
            user_partition_id=user_partition_id, group_id=group_id
        )

    def test_non_staff(self):
        """
        Verify that we cannot access cohort_handler if we're a non-staff user.
        """
        self._verify_non_staff_cannot_access(cohort_handler, "GET", [unicode(self.course.id)])
        self._verify_non_staff_cannot_access(cohort_handler, "POST", [unicode(self.course.id)])
        self._verify_non_staff_cannot_access(cohort_handler, "PUT", [unicode(self.course.id)])

    def test_no_cohorts(self):
        """
        Verify that no cohorts are in response for a course with no cohorts.
        """
        self.verify_lists_expected_cohorts([])

    def test_some_cohorts(self):
        """
        Verify that cohorts are in response for a course with some cohorts.
        """
        self._create_cohorts()
        expected_cohorts = [
            CohortHandlerTestCase.create_expected_cohort(self.cohort1, 3, CohortAssignmentType.NONE),
            CohortHandlerTestCase.create_expected_cohort(self.cohort2, 2, CohortAssignmentType.NONE),
            CohortHandlerTestCase.create_expected_cohort(self.cohort3, 2, CohortAssignmentType.NONE),
        ]
        self.verify_lists_expected_cohorts(expected_cohorts)

    def test_auto_cohorts(self):
        """
        Verify that auto cohorts are included in the response.
        """
        config_course_cohorts(self.course, [], cohorted=True,
                              auto_cohort_groups=["AutoGroup1", "AutoGroup2"])

        # Will create cohort1, cohort2, and cohort3. Auto cohorts remain uncreated.
        self._create_cohorts()
        # Get the cohorts from the course, which will cause auto cohorts to be created.
        actual_cohorts = self.get_cohort_handler(self.course)
        # Get references to the created auto cohorts.
        auto_cohort_1 = get_cohort_by_name(self.course.id, "AutoGroup1")
        auto_cohort_2 = get_cohort_by_name(self.course.id, "AutoGroup2")
        expected_cohorts = [
            CohortHandlerTestCase.create_expected_cohort(self.cohort1, 3, CohortAssignmentType.NONE),
            CohortHandlerTestCase.create_expected_cohort(self.cohort2, 2, CohortAssignmentType.NONE),
            CohortHandlerTestCase.create_expected_cohort(self.cohort3, 2, CohortAssignmentType.NONE),
            CohortHandlerTestCase.create_expected_cohort(auto_cohort_1, 0, CohortAssignmentType.RANDOM),
            CohortHandlerTestCase.create_expected_cohort(auto_cohort_2, 0, CohortAssignmentType.RANDOM),
        ]
        self.verify_lists_expected_cohorts(expected_cohorts, actual_cohorts)

    def test_default_cohort(self):
        """
        Verify that the default cohort is not created and included in the response until students are assigned to it.
        """
        # verify the default cohort is not created when the course is not cohorted
        self.verify_lists_expected_cohorts([])

        # create a cohorted course without any auto_cohort_groups
        config_course_cohorts(self.course, [], cohorted=True)

        # verify the default cohort is not yet created until a user is assigned
        self.verify_lists_expected_cohorts([])

        # create enrolled users
        users = [UserFactory() for _ in range(3)]
        self._enroll_users(users, self.course.id)

        # mimic users accessing the discussion forum
        for user in users:
            get_cohort(user, self.course.id)

        # verify the default cohort is automatically created
        default_cohort = get_cohort_by_name(self.course.id, DEFAULT_COHORT_NAME)
        actual_cohorts = self.get_cohort_handler(self.course)
        self.verify_lists_expected_cohorts(
            [CohortHandlerTestCase.create_expected_cohort(default_cohort, len(users), CohortAssignmentType.RANDOM)],
            actual_cohorts,
        )

        # set auto_cohort_groups and verify the default cohort is no longer listed as RANDOM
        config_course_cohorts(self.course, [], cohorted=True, auto_cohort_groups=["AutoGroup"])
        actual_cohorts = self.get_cohort_handler(self.course)
        auto_cohort = get_cohort_by_name(self.course.id, "AutoGroup")
        self.verify_lists_expected_cohorts(
            [
                CohortHandlerTestCase.create_expected_cohort(default_cohort, len(users), CohortAssignmentType.NONE),
                CohortHandlerTestCase.create_expected_cohort(auto_cohort, 0, CohortAssignmentType.RANDOM),
            ],
            actual_cohorts,
        )

    def test_get_single_cohort(self):
        """
        Tests that information for just a single cohort can be requested.
        """
        self._create_cohorts()
        response_dict = self.get_cohort_handler(self.course, self.cohort2)
        self.assertEqual(
            response_dict,
            {
                "name": self.cohort2.name,
                "id": self.cohort2.id,
                "user_count": 2,
                "assignment_type": "none",
                "user_partition_id": None,
                "group_id": None
            }
        )

    ############### Tests of adding a new cohort ###############

    def verify_contains_added_cohort(
            self, response_dict, cohort_name, expected_user_partition_id=None, expected_group_id=None
    ):
        """
        Verifies that the cohort was created properly and the correct response was returned.
        """
        created_cohort = get_cohort_by_name(self.course.id, cohort_name)
        self.assertIsNotNone(created_cohort)
        self.assertEqual(
            response_dict,
            {
                "name": cohort_name,
                "id": created_cohort.id,
                "user_count": 0,
                "assignment_type": CohortAssignmentType.NONE,
                "user_partition_id": expected_user_partition_id,
                "group_id": expected_group_id
            }
        )
        self.assertEqual((expected_group_id, expected_user_partition_id), get_group_info_for_cohort(created_cohort))

    def test_create_new_cohort(self):
        """
        Verify that a new cohort can be created, with and without user_partition_id/group_id information.
        """
        new_cohort_name = "New cohort unassociated to content groups"
        response_dict = self.put_cohort_handler(self.course, data={'name': new_cohort_name})
        self.verify_contains_added_cohort(response_dict, new_cohort_name)

        new_cohort_name = "New cohort linked to group"
        response_dict = self.put_cohort_handler(
            self.course, data={'name': new_cohort_name, 'user_partition_id': 1, 'group_id': 2}
        )
        self.verify_contains_added_cohort(response_dict, new_cohort_name, 1, 2)

    def test_create_new_cohort_missing_name(self):
        """
        Verify that we cannot create a cohort without specifying a name.
        """
        response_dict = self.put_cohort_handler(self.course, expected_response_code=400)
        self.assertEqual("In order to create a cohort, a name must be specified.", response_dict.get("error"))

    def test_create_new_cohort_existing_name(self):
        """
        Verify that we cannot add a cohort with the same name as an existing cohort.
        """
        self._create_cohorts()
        response_dict = self.put_cohort_handler(
            self.course, data={'name': self.cohort1.name}, expected_response_code=400
        )
        self.assertEqual("You cannot create two cohorts with the same name", response_dict.get("error"))

    def test_create_new_cohort_missing_user_partition_id(self):
        """
        Verify that we cannot create a cohort with a group_id if the user_partition_id is not also specified.
        """
        response_dict = self.put_cohort_handler(
            self.course, data={'name': "Cohort missing user_partition_id", 'group_id': 2}, expected_response_code=400
        )
        self.assertEqual(
            "If group_id is specified, user_partition_id must also be specified.", response_dict.get("error")
        )

    ############### Tests of updating an existing cohort ###############

    def test_update_manual_cohort_name(self):
        """
        Test that it is possible to update the name of an existing manual cohort.
        """
        self._create_cohorts()
        updated_name = self.cohort1.name + "_updated"
        response_dict = self.put_cohort_handler(self.course, self.cohort1, {'name': updated_name})
        self.assertEqual(updated_name, get_cohort_by_id(self.course.id, self.cohort1.id).name)
        self.assertEqual(updated_name, response_dict.get("name"))
        self.assertEqual(CohortAssignmentType.NONE, response_dict.get("assignment_type"))
        self.assertEqual(CohortAssignmentType.NONE, CohortAssignmentType.get(self.cohort1, self.course))

    def test_update_random_cohort_name_not_supported(self):
        """
        Test that it is not possible to update the name of an existing random cohort.
        """
        random_cohort = CohortFactory(course_id=self.course.id)
        random_cohort_name = random_cohort.name

        # Update course cohort_config so random_cohort is in the list of auto cohorts.
        self.course.cohort_config["auto_cohort_groups"] = [random_cohort_name]
        modulestore().update_item(self.course, self.staff_user.id)

        updated_name = random_cohort.name + "_updated"
        response_dict = self.put_cohort_handler(
            self.course, random_cohort, {'name': updated_name}, expected_response_code=400
        )
        self.assertEqual(
            "Renaming of random cohorts is not supported at this time.", response_dict.get("error")
        )
        self.assertEqual(random_cohort_name, get_cohort_by_id(self.course.id, random_cohort.id).name)
        self.assertEqual(CohortAssignmentType.RANDOM, CohortAssignmentType.get(random_cohort, self.course))

    def test_update_cohort_group_id(self):
        """
        Test that it is possible to update the user_partition_id/group_id of an existing cohort.
        """
        self._create_cohorts()
        self.assertEqual((None, None), get_group_info_for_cohort(self.cohort1))
        response_dict = self.put_cohort_handler(
            self.course, self.cohort1, data={'name': self.cohort1.name, 'group_id': 2, 'user_partition_id': 3}
        )
        self.assertEqual((2, 3), get_group_info_for_cohort(self.cohort1))
        self.assertEqual(2, response_dict.get("group_id"))
        self.assertEqual(3, response_dict.get("user_partition_id"))
        # Check that the name didn't change.
        self.assertEqual(self.cohort1.name, response_dict.get("name"))

    def test_update_cohort_remove_group_id(self):
        """
        Test that it is possible to remove the user_partition_id/group_id linking of an existing cohort.
        """
        self._create_cohorts()
        link_cohort_to_partition_group(self.cohort1, 5, 0)
        self.assertEqual((0, 5), get_group_info_for_cohort(self.cohort1))
        response_dict = self.put_cohort_handler(
            self.course, self.cohort1, data={'name': self.cohort1.name, 'group_id': None}
        )
        self.assertEqual((None, None), get_group_info_for_cohort(self.cohort1))
        self.assertIsNone(response_dict.get("group_id"))
        self.assertIsNone(response_dict.get("user_partition_id"))

    def test_change_cohort_group_id(self):
        """
        Test that it is possible to change the user_partition_id/group_id of an existing cohort to a
        different group_id.
        """
        self._create_cohorts()
        self.assertEqual((None, None), get_group_info_for_cohort(self.cohort1))
        self.put_cohort_handler(
            self.course, self.cohort1, data={'name': self.cohort1.name, 'group_id': 2, 'user_partition_id': 3}
        )
        self.assertEqual((2, 3), get_group_info_for_cohort(self.cohort1))
        self.put_cohort_handler(
            self.course, self.cohort1, data={'name': self.cohort1.name, 'group_id': 1, 'user_partition_id': 3}
        )
        self.assertEqual((1, 3), get_group_info_for_cohort(self.cohort1))

    def test_update_cohort_missing_user_partition_id(self):
        """
        Verify that we cannot update a cohort with a group_id if the user_partition_id is not also specified.
        """
        self._create_cohorts()
        response_dict = self.put_cohort_handler(
            self.course, self.cohort1, data={'name': self.cohort1.name, 'group_id': 2}, expected_response_code=400
        )
        self.assertEqual(
            "If group_id is specified, user_partition_id must also be specified.", response_dict.get("error")
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
        response = users_in_cohort(request, unicode(course.id), cohort.id)

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
        self.assertEqual(len(returned_users), len(expected_users))
        self.assertEqual(set(returned_users), set(expected_users))
        self.assertTrue(set(returned_users).issubset(cohort.users.all()))

    def test_non_staff(self):
        """
        Verify that non-staff users cannot access `check_users_in_cohort`.
        """
        cohort = CohortFactory(course_id=self.course.id, users=[])
        self._verify_non_staff_cannot_access(users_in_cohort, "GET", [unicode(self.course.id), cohort.id])

    def test_no_users(self):
        """
        Verify that we don't get back any users for a cohort with no users.
        """
        cohort = CohortFactory(course_id=self.course.id, users=[])
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
        users = [UserFactory() for _ in range(5)]
        cohort = CohortFactory(course_id=self.course.id, users=users)
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
        users = [UserFactory() for _ in range(101)]
        cohort = CohortFactory(course_id=self.course.id, users=users)
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
        users = [UserFactory() for _ in range(5)]
        cohort = CohortFactory(course_id=self.course.id, users=users)
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
        users = [UserFactory() for _ in range(5)]
        cohort = CohortFactory(course_id=self.course.id, users=users)
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
                lambda: add_users_to_cohort(request, unicode(course.id), cohort.id)
            )
        else:
            response = add_users_to_cohort(request, unicode(course.id), cohort.id)
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
        self.assertEqual(
            response_dict.get("added"),
            [
                {"username": user.username, "name": user.profile.name, "email": user.email}
                for user in expected_added
            ]
        )
        self.assertEqual(
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
        self.assertEqual(
            response_dict.get("present"),
            [username_or_email for (_, username_or_email) in expected_present]
        )
        self.assertEqual(response_dict.get("unknown"), expected_unknown)
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
        cohort = CohortFactory(course_id=self.course.id, users=[])
        self._verify_non_staff_cannot_access(
            add_users_to_cohort,
            "POST",
            [unicode(self.course.id), cohort.id]
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
        users = [UserFactory(username="user{0}".format(i)) for i in range(3)]
        usernames = [user.username for user in users]
        wrong_course_key = SlashSeparatedCourseKey("some", "arbitrary", "course")
        wrong_course_cohort = CohortFactory(name="wrong_cohort", course_id=wrong_course_key, users=[])
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
        response = remove_user_from_cohort(request, unicode(self.course.id), cohort.id)
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
        cohort = CohortFactory(course_id=self.course.id, users=[])
        self._verify_non_staff_cannot_access(
            remove_user_from_cohort,
            "POST",
            [unicode(self.course.id), cohort.id]
        )

    def test_no_username_given(self):
        """
        Verify that we get an error message when omitting a username.
        """
        cohort = CohortFactory(course_id=self.course.id, users=[])
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
        cohort = CohortFactory(course_id=self.course.id, users=[])
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
        user = UserFactory()
        cohort = CohortFactory(course_id=self.course.id, users=[])
        response_dict = self.request_remove_user_from_cohort(user.username, cohort)
        self.verify_removed_user_from_cohort(user.username, response_dict, cohort)

    def test_can_remove_user_from_cohort(self):
        """
        Verify that we can remove a user from a cohort.
        """
        user = UserFactory()
        cohort = CohortFactory(course_id=self.course.id, users=[user])
        response_dict = self.request_remove_user_from_cohort(user.username, cohort)
        self.verify_removed_user_from_cohort(user.username, response_dict, cohort)
