import json

from django.test.client import RequestFactory
from django.test.utils import override_settings
from factory import post_generation, Sequence
from factory.django import DjangoModelFactory

from course_groups.models import CourseUserGroup
from course_groups.views import add_users_to_cohort
from courseware.tests.tests import TEST_DATA_MIXED_MODULESTORE
from student.tests.factories import UserFactory
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class CohortFactory(DjangoModelFactory):
    FACTORY_FOR = CourseUserGroup

    name = Sequence("cohort{}".format)
    course_id = "dummy_id"
    group_type = CourseUserGroup.COHORT

    @post_generation
    def users(self, create, extracted, **kwargs):  # pylint: disable=W0613
        self.users.add(*extracted)


@override_settings(MODULESTORE=TEST_DATA_MIXED_MODULESTORE)
class AddUsersToCohortTestCase(ModuleStoreTestCase):
    def setUp(self):
        self.course = CourseFactory.create()
        self.staff_user = UserFactory.create(is_staff=True)
        self.cohort1_users = [UserFactory.create() for _ in range(3)]
        self.cohort2_users = [UserFactory.create() for _ in range(2)]
        self.cohort3_users = [UserFactory.create() for _ in range(2)]
        self.cohortless_users = [UserFactory.create() for _ in range(3)]
        self.cohort1 = CohortFactory.create(course_id=self.course.id, users=self.cohort1_users)
        self.cohort2 = CohortFactory.create(course_id=self.course.id, users=self.cohort2_users)
        self.cohort3 = CohortFactory.create(course_id=self.course.id, users=self.cohort3_users)

    def check_request(
            self,
            users_string,
            expected_added=None,
            expected_changed=None,
            expected_present=None,
            expected_unknown=None
    ):
        """
        Check that add_users_to_cohort returns the expected result and has the
        expected side effects. The given users will be added to cohort1.

        users_string is the string input entered by the client

        expected_added is a list of users

        expected_changed is a list of (user, previous_cohort) tuples

        expected_present is a list of (user, email/username) tuples where
        email/username corresponds to the input

        expected_unknown is a list of strings corresponding to the input
        """
        expected_added = expected_added or []
        expected_changed = expected_changed or []
        expected_present = expected_present or []
        expected_unknown = expected_unknown or []
        request = RequestFactory().post("dummy_url", {"users": users_string})
        request.user = self.staff_user
        response = add_users_to_cohort(request, self.course.id.to_deprecated_string(), self.cohort1.id)
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.content)
        self.assertEqual(result.get("success"), True)
        self.assertItemsEqual(
            result.get("added"),
            [
                {"username": user.username, "name": user.profile.name, "email": user.email}
                for user in expected_added
            ]
        )
        self.assertItemsEqual(
            result.get("changed"),
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
            result.get("present"),
            [username_or_email for (_, username_or_email) in expected_present]
        )
        self.assertItemsEqual(result.get("unknown"), expected_unknown)
        for user in expected_added + [user for (user, _) in expected_changed + expected_present]:
            self.assertEqual(
                CourseUserGroup.objects.get(
                    course_id=self.course.id,
                    group_type=CourseUserGroup.COHORT,
                    users__id=user.id
                ),
                self.cohort1
            )

    def test_empty(self):
        self.check_request("")

    def test_only_added(self):
        self.check_request(
            ",".join([user.username for user in self.cohortless_users]),
            expected_added=self.cohortless_users
        )

    def test_only_changed(self):
        self.check_request(
            ",".join([user.username for user in self.cohort2_users + self.cohort3_users]),
            expected_changed=(
                [(user, self.cohort2.name) for user in self.cohort2_users] +
                [(user, self.cohort3.name) for user in self.cohort3_users]
            )
        )

    def test_only_present(self):
        usernames = [user.username for user in self.cohort1_users]
        self.check_request(
            ",".join(usernames),
            expected_present=[(user, user.username) for user in self.cohort1_users]
        )

    def test_only_unknown(self):
        usernames = ["unknown_user{}".format(i) for i in range(3)]
        self.check_request(
            ",".join(usernames),
            expected_unknown=usernames
        )

    def test_all(self):
        unknowns = ["unknown_user{}".format(i) for i in range(3)]
        self.check_request(
            ",".join(
                unknowns +
                [
                    user.username
                    for user in self.cohortless_users + self.cohort1_users + self.cohort2_users + self.cohort3_users
                ]
            ),
            self.cohortless_users,
            (
                [(user, self.cohort2.name) for user in self.cohort2_users] +
                [(user, self.cohort3.name) for user in self.cohort3_users]
            ),
            [(user, user.username) for user in self.cohort1_users],
            unknowns
        )

    def test_emails(self):
        unknown = "unknown_user@example.com"
        self.check_request(
            ",".join([
                self.cohort1_users[0].email,
                self.cohort2_users[0].email,
                self.cohortless_users[0].email,
                unknown
            ]),
            [self.cohortless_users[0]],
            [(self.cohort2_users[0], self.cohort2.name)],
            [(self.cohort1_users[0], self.cohort1_users[0].email)],
            [unknown]
        )

    def test_delimiters(self):
        unknown = "unknown_user"
        self.check_request(
            " {} {}\t{}, \r\n{}".format(
                unknown,
                self.cohort1_users[0].username,
                self.cohort2_users[0].username,
                self.cohortless_users[0].username
            ),
            [self.cohortless_users[0]],
            [(self.cohort2_users[0], self.cohort2.name)],
            [(self.cohort1_users[0], self.cohort1_users[0].username)],
            [unknown]
        )
