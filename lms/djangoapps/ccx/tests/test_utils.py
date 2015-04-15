"""
test utils
"""
from ccx.models import (  # pylint: disable=import-error
    CcxMembership,
    CcxFutureMembership,
)
from ccx.tests.factories import (  # pylint: disable=import-error
    CcxFactory,
    CcxMembershipFactory,
    CcxFutureMembershipFactory,
)
from student.roles import CourseCcxCoachRole  # pylint: disable=import-error
from student.tests.factories import (  # pylint: disable=import-error
    AdminFactory,
    UserFactory,
    CourseEnrollmentFactory,
    AnonymousUserFactory,
)
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory


class TestEmailEnrollmentState(ModuleStoreTestCase):
    """unit tests for the EmailEnrollmentState class
    """

    def setUp(self):
        """
        Set up tests
        """
        super(TestEmailEnrollmentState, self).setUp()
        # remove user provided by the parent test case so we can make our own
        # when needed.
        self.user = None
        course = CourseFactory.create()
        coach = AdminFactory.create()
        role = CourseCcxCoachRole(course.id)
        role.add_users(coach)
        self.ccx = CcxFactory(course_id=course.id, coach=coach)

    def create_user(self):
        """provide a legitimate django user for testing
        """
        if getattr(self, 'user', None) is None:
            self.user = UserFactory()

    def register_user_in_ccx(self):
        """create registration of self.user in self.ccx

        registration will be inactive
        """
        self.create_user()
        CcxMembershipFactory(ccx=self.ccx, student=self.user)

    def create_one(self, email=None):
        """Create a single EmailEnrollmentState object and return it
        """
        from ccx.utils import EmailEnrollmentState  # pylint: disable=import-error
        if email is None:
            email = self.user.email
        return EmailEnrollmentState(self.ccx, email)

    def test_enrollment_state_for_non_user(self):
        """verify behavior for non-user email address
        """
        ee_state = self.create_one(email='nobody@nowhere.com')
        for attr in ['user', 'member', 'full_name', 'in_ccx']:
            value = getattr(ee_state, attr, 'missing attribute')
            self.assertFalse(value, "{}: {}".format(value, attr))

    def test_enrollment_state_for_non_member_user(self):
        """verify behavior for email address of user who is not a ccx memeber
        """
        self.create_user()
        ee_state = self.create_one()
        self.assertTrue(ee_state.user)
        self.assertFalse(ee_state.in_ccx)
        self.assertEqual(ee_state.member, self.user)
        self.assertEqual(ee_state.full_name, self.user.profile.name)

    def test_enrollment_state_for_member_user(self):
        """verify behavior for email address of user who is a ccx member
        """
        self.create_user()
        self.register_user_in_ccx()
        ee_state = self.create_one()
        for attr in ['user', 'in_ccx']:
            self.assertTrue(
                getattr(ee_state, attr, False),
                "attribute {} is missing or False".format(attr)
            )
        self.assertEqual(ee_state.member, self.user)
        self.assertEqual(ee_state.full_name, self.user.profile.name)

    def test_enrollment_state_to_dict(self):
        """verify dict representation of EmailEnrollmentState
        """
        self.create_user()
        self.register_user_in_ccx()
        ee_state = self.create_one()
        ee_dict = ee_state.to_dict()
        expected = {
            'user': True,
            'member': self.user,
            'in_ccx': True,
        }
        for expected_key, expected_value in expected.iteritems():
            self.assertTrue(expected_key in ee_dict)
            self.assertEqual(expected_value, ee_dict[expected_key])

    def test_enrollment_state_repr(self):
        self.create_user()
        self.register_user_in_ccx()
        ee_state = self.create_one()
        representation = repr(ee_state)
        self.assertTrue('user=True' in representation)
        self.assertTrue('in_ccx=True' in representation)
        member = 'member={}'.format(self.user)
        self.assertTrue(member in representation)


# TODO: deal with changes in behavior for auto_enroll
class TestGetEmailParams(ModuleStoreTestCase):
    """tests for ccx.utils.get_email_params
    """
    def setUp(self):
        """
        Set up tests
        """
        super(TestGetEmailParams, self).setUp()
        course = CourseFactory.create()
        coach = AdminFactory.create()
        role = CourseCcxCoachRole(course.id)
        role.add_users(coach)
        self.ccx = CcxFactory(course_id=course.id, coach=coach)
        self.all_keys = [
            'site_name', 'course', 'course_url', 'registration_url',
            'course_about_url', 'auto_enroll'
        ]
        self.url_keys = [k for k in self.all_keys if 'url' in k]
        self.course_keys = [k for k in self.url_keys if 'course' in k]

    def call_fut(self, auto_enroll=False, secure=False):
        """
        call function under test
        """
        from ccx.utils import get_email_params  # pylint: disable=import-error
        return get_email_params(self.ccx, auto_enroll, secure)

    def test_params_have_expected_keys(self):
        params = self.call_fut()
        self.assertFalse(set(params.keys()) - set(self.all_keys))

    def test_ccx_id_in_params(self):
        expected_course_id = self.ccx.course_id.to_deprecated_string()
        params = self.call_fut()
        self.assertEqual(params['course'], self.ccx)
        for url_key in self.url_keys:
            self.assertTrue('http://' in params[url_key])
        for url_key in self.course_keys:
            self.assertTrue(expected_course_id in params[url_key])

    def test_security_respected(self):
        secure = self.call_fut(secure=True)
        for url_key in self.url_keys:
            self.assertTrue('https://' in secure[url_key])
        insecure = self.call_fut(secure=False)
        for url_key in self.url_keys:
            self.assertTrue('http://' in insecure[url_key])

    def test_auto_enroll_passed_correctly(self):
        not_auto = self.call_fut(auto_enroll=False)
        self.assertFalse(not_auto['auto_enroll'])
        auto = self.call_fut(auto_enroll=True)
        self.assertTrue(auto['auto_enroll'])


# TODO: deal with changes in behavior for auto_enroll
class TestEnrollEmail(ModuleStoreTestCase):
    """tests for the enroll_email function from ccx.utils
    """
    def setUp(self):
        super(TestEnrollEmail, self).setUp()
        # unbind the user created by the parent, so we can create our own when
        # needed.
        self.user = None
        course = CourseFactory.create()
        coach = AdminFactory.create()
        role = CourseCcxCoachRole(course.id)
        role.add_users(coach)
        self.ccx = CcxFactory(course_id=course.id, coach=coach)
        self.outbox = self.get_outbox()

    def create_user(self):
        """provide a legitimate django user for testing
        """
        if getattr(self, 'user', None) is None:
            self.user = UserFactory()

    def register_user_in_ccx(self):
        """create registration of self.user in self.ccx

        registration will be inactive
        """
        self.create_user()
        CcxMembershipFactory(ccx=self.ccx, student=self.user)

    def get_outbox(self):
        """Return the django mail outbox"""
        from django.core import mail
        return mail.outbox

    def check_membership(self, email=None, user=None, future=False):
        """Verify tjat an appropriate CCX Membership exists"""
        if not email and not user:
            self.fail(
                "must provide user or email address to check CCX Membership"
            )
        if future and email:
            membership = CcxFutureMembership.objects.filter(
                ccx=self.ccx, email=email
            )
        elif not future:
            if not user:
                user = self.user
            membership = CcxMembership.objects.filter(
                ccx=self.ccx, student=user
            )
        self.assertTrue(membership.exists())

    def check_enrollment_state(self, state, in_ccx, member, user):
        """Verify an enrollment state object against provided arguments

        state.in_ccx will always be a boolean
        state.user will always be a boolean
        state.member will be a Django user object or None
        """
        self.assertEqual(in_ccx, state.in_ccx)
        self.assertEqual(member, state.member)
        self.assertEqual(user, state.user)

    def call_fut(
            self,
            student_email=None,
            auto_enroll=False,
            email_students=False,
            email_params=None
    ):
        """Call function under test"""
        from ccx.utils import enroll_email  # pylint: disable=import-error
        if student_email is None:
            student_email = self.user.email
        before, after = enroll_email(
            self.ccx, student_email, auto_enroll, email_students, email_params
        )
        return before, after

    def test_enroll_non_user_sending_email(self):
        """enroll a non-user email and send an enrollment email to them
        """
        # ensure no emails are in the outbox now
        self.assertEqual(self.outbox, [])
        test_email = "nobody@nowhere.com"
        before, after = self.call_fut(
            student_email=test_email, email_students=True
        )

        # there should be a future membership set for this email address now
        self.check_membership(email=test_email, future=True)
        for state in [before, after]:
            self.check_enrollment_state(state, False, None, False)
        # mail was sent and to the right person
        self.assertEqual(len(self.outbox), 1)
        msg = self.outbox[0]
        self.assertTrue(test_email in msg.recipients())

    def test_enroll_non_member_sending_email(self):
        """register a non-member and send an enrollment email to them
        """
        self.create_user()
        # ensure no emails are in the outbox now
        self.assertEqual(self.outbox, [])
        before, after = self.call_fut(email_students=True)

        # there should be a membership set for this email address now
        self.check_membership(email=self.user.email)
        self.check_enrollment_state(before, False, self.user, True)
        self.check_enrollment_state(after, True, self.user, True)
        # mail was sent and to the right person
        self.assertEqual(len(self.outbox), 1)
        msg = self.outbox[0]
        self.assertTrue(self.user.email in msg.recipients())

    def test_enroll_member_sending_email(self):
        """register a member and send an enrollment email to them
        """
        self.register_user_in_ccx()
        # ensure no emails are in the outbox now
        self.assertEqual(self.outbox, [])
        before, after = self.call_fut(email_students=True)

        # there should be a membership set for this email address now
        self.check_membership(email=self.user.email)
        for state in [before, after]:
            self.check_enrollment_state(state, True, self.user, True)
        # mail was sent and to the right person
        self.assertEqual(len(self.outbox), 1)
        msg = self.outbox[0]
        self.assertTrue(self.user.email in msg.recipients())

    def test_enroll_non_user_no_email(self):
        """register a non-user via email address but send no email
        """
        # ensure no emails are in the outbox now
        self.assertEqual(self.outbox, [])
        test_email = "nobody@nowhere.com"
        before, after = self.call_fut(
            student_email=test_email, email_students=False
        )

        # there should be a future membership set for this email address now
        self.check_membership(email=test_email, future=True)
        for state in [before, after]:
            self.check_enrollment_state(state, False, None, False)
        # ensure there are still no emails in the outbox now
        self.assertEqual(self.outbox, [])

    def test_enroll_non_member_no_email(self):
        """register a non-member but send no email"""
        self.create_user()
        # ensure no emails are in the outbox now
        self.assertEqual(self.outbox, [])
        before, after = self.call_fut(email_students=False)

        # there should be a membership set for this email address now
        self.check_membership(email=self.user.email)
        self.check_enrollment_state(before, False, self.user, True)
        self.check_enrollment_state(after, True, self.user, True)
        # ensure there are still no emails in the outbox now
        self.assertEqual(self.outbox, [])

    def test_enroll_member_no_email(self):
        """enroll a member but send no email
        """
        self.register_user_in_ccx()
        # ensure no emails are in the outbox now
        self.assertEqual(self.outbox, [])
        before, after = self.call_fut(email_students=False)

        # there should be a membership set for this email address now
        self.check_membership(email=self.user.email)
        for state in [before, after]:
            self.check_enrollment_state(state, True, self.user, True)
        # ensure there are still no emails in the outbox now
        self.assertEqual(self.outbox, [])


# TODO: deal with changes in behavior for auto_enroll
class TestUnenrollEmail(ModuleStoreTestCase):
    """Tests for the unenroll_email function from ccx.utils"""
    def setUp(self):
        super(TestUnenrollEmail, self).setUp()
        # unbind the user created by the parent, so we can create our own when
        # needed.
        self.user = None
        course = CourseFactory.create()
        coach = AdminFactory.create()
        role = CourseCcxCoachRole(course.id)
        role.add_users(coach)
        self.ccx = CcxFactory(course_id=course.id, coach=coach)
        self.outbox = self.get_outbox()
        self.email = "nobody@nowhere.com"

    def get_outbox(self):
        """Return the django mail outbox"""
        from django.core import mail
        return mail.outbox

    def create_user(self):
        """provide a legitimate django user for testing
        """
        if getattr(self, 'user', None) is None:
            self.user = UserFactory()

    def make_ccx_membership(self):
        """create registration of self.user in self.ccx

        registration will be inactive
        """
        self.create_user()
        CcxMembershipFactory.create(ccx=self.ccx, student=self.user)

    def make_ccx_future_membership(self):
        """create future registration for email in self.ccx"""
        CcxFutureMembershipFactory.create(
            ccx=self.ccx, email=self.email
        )

    def check_enrollment_state(self, state, in_ccx, member, user):
        """Verify an enrollment state object against provided arguments

        state.in_ccx will always be a boolean
        state.user will always be a boolean
        state.member will be a Django user object or None
        """
        self.assertEqual(in_ccx, state.in_ccx)
        self.assertEqual(member, state.member)
        self.assertEqual(user, state.user)

    def check_membership(self, future=False):
        """
        check membership
        """
        if future:
            membership = CcxFutureMembership.objects.filter(
                ccx=self.ccx, email=self.email
            )
        else:
            membership = CcxMembership.objects.filter(
                ccx=self.ccx, student=self.user
            )
        return membership.exists()

    def call_fut(self, email_students=False):
        """call function under test"""
        from ccx.utils import unenroll_email  # pylint: disable=import-error
        email = getattr(self, 'user', None) and self.user.email or self.email
        return unenroll_email(self.ccx, email, email_students=email_students)

    def test_unenroll_future_member_with_email(self):
        """unenroll a future member and send an email
        """
        self.make_ccx_future_membership()
        # assert that a membership exists and that no emails have been sent
        self.assertTrue(self.check_membership(future=True))
        self.assertEqual(self.outbox, [])
        # unenroll the student
        before, after = self.call_fut(email_students=True)

        # assert that membership is now gone
        self.assertFalse(self.check_membership(future=True))
        # validate the before and after enrollment states
        for state in [before, after]:
            self.check_enrollment_state(state, False, None, False)
        # check that mail was sent and to the right person
        self.assertEqual(len(self.outbox), 1)
        msg = self.outbox[0]
        self.assertTrue(self.email in msg.recipients())

    def test_unenroll_member_with_email(self):
        """unenroll a current member and send an email"""
        self.make_ccx_membership()
        # assert that a membership exists and that no emails have been sent
        self.assertTrue(self.check_membership())
        self.assertEqual(self.outbox, [])
        # unenroll the student
        before, after = self.call_fut(email_students=True)

        # assert that membership is now gone
        self.assertFalse(self.check_membership())
        # validate the before and after enrollment state
        self.check_enrollment_state(after, False, self.user, True)
        self.check_enrollment_state(before, True, self.user, True)
        # check that mail was sent and to the right person
        self.assertEqual(len(self.outbox), 1)
        msg = self.outbox[0]
        self.assertTrue(self.user.email in msg.recipients())

    def test_unenroll_future_member_no_email(self):
        """unenroll a future member but send no email
        """
        self.make_ccx_future_membership()
        # assert that a membership exists and that no emails have been sent
        self.assertTrue(self.check_membership(future=True))
        self.assertEqual(self.outbox, [])
        # unenroll the student
        before, after = self.call_fut()

        # assert that membership is now gone
        self.assertFalse(self.check_membership(future=True))
        # validate the before and after enrollment states
        for state in [before, after]:
            self.check_enrollment_state(state, False, None, False)
        # no email was sent to the student
        self.assertEqual(self.outbox, [])

    def test_unenroll_member_no_email(self):
        """unenroll a current member but send no email
        """
        self.make_ccx_membership()
        # assert that a membership exists and that no emails have been sent
        self.assertTrue(self.check_membership())
        self.assertEqual(self.outbox, [])
        # unenroll the student
        before, after = self.call_fut()

        # assert that membership is now gone
        self.assertFalse(self.check_membership())
        # validate the before and after enrollment state
        self.check_enrollment_state(after, False, self.user, True)
        self.check_enrollment_state(before, True, self.user, True)
        # no email was sent to the student
        self.assertEqual(self.outbox, [])


class TestUserCCXList(ModuleStoreTestCase):
    """Unit tests for ccx.utils.get_all_ccx_for_user"""

    def setUp(self):
        """Create required infrastructure for tests"""
        super(TestUserCCXList, self).setUp()
        self.course = CourseFactory.create()
        coach = AdminFactory.create()
        role = CourseCcxCoachRole(self.course.id)
        role.add_users(coach)
        self.ccx = CcxFactory(course_id=self.course.id, coach=coach)
        enrollment = CourseEnrollmentFactory.create(course_id=self.course.id)
        self.user = enrollment.user
        self.anonymous = AnonymousUserFactory.create()

    def register_user_in_ccx(self, active=False):
        """create registration of self.user in self.ccx

        registration will be inactive unless active=True
        """
        CcxMembershipFactory(ccx=self.ccx, student=self.user, active=active)

    def get_course_title(self):
        """Get course title"""
        from courseware.courses import get_course_about_section  # pylint: disable=import-error
        return get_course_about_section(self.course, 'title')

    def call_fut(self, user):
        """Call function under test"""
        from ccx.utils import get_all_ccx_for_user  # pylint: disable=import-error
        return get_all_ccx_for_user(user)

    def test_anonymous_sees_no_ccx(self):
        memberships = self.call_fut(self.anonymous)
        self.assertEqual(memberships, [])

    def test_unenrolled_sees_no_ccx(self):
        memberships = self.call_fut(self.user)
        self.assertEqual(memberships, [])

    def test_enrolled_inactive_sees_no_ccx(self):
        self.register_user_in_ccx()
        memberships = self.call_fut(self.user)
        self.assertEqual(memberships, [])

    def test_enrolled_sees_a_ccx(self):
        self.register_user_in_ccx(active=True)
        memberships = self.call_fut(self.user)
        self.assertEqual(len(memberships), 1)

    def test_data_structure(self):
        self.register_user_in_ccx(active=True)
        memberships = self.call_fut(self.user)
        this_membership = memberships[0]
        self.assertTrue(this_membership)
        # structure contains the expected keys
        for key in ['ccx_name', 'ccx_url']:
            self.assertTrue(key in this_membership.keys())
        url_parts = [self.course.id.to_deprecated_string(), str(self.ccx.id)]
        # all parts of the ccx url are present
        for part in url_parts:
            self.assertTrue(part in this_membership['ccx_url'])
        actual_name = self.ccx.display_name
        self.assertEqual(actual_name, this_membership['ccx_name'])
