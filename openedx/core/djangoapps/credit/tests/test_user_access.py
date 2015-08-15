# -*- coding: utf-8 -*-
"""
Tests for checking user access on ICRV and content blocks
"""

import ddt
import unittest

from django.conf import settings

from lms.djangoapps.courseware.access import _has_group_access
from lms.djangoapps.verify_student.models import (
    VerificationCheckpoint,
    VerificationStatus,
    SkippedReverification,
)
from student.models import CourseEnrollment
from student.tests.factories import UserFactory
from openedx.core.djangoapps.credit.signals import on_course_publish
from xmodule.modulestore.tests.django_utils import ModuleStoreTestCase
from xmodule.modulestore.tests.factories import CourseFactory, ItemFactory
from xmodule.modulestore.django import modulestore


@ddt.ddt
@unittest.skipUnless(settings.ROOT_URLCONF == 'lms.urls', 'Test only valid in lms')
class UserAccessToContent(ModuleStoreTestCase):
    """Test for Reverification Partition Scheme user access to content."""

    SUBMITTED = "submitted"
    APPROVED = "approved"
    DENIED = "denied"
    SKIPPED = "skipped"

    def add_verification_status(self, user, status):
        """Adding the verification status for a user."""

        VerificationStatus.add_status_from_checkpoints(
            checkpoints=[self.first_checkpoint],
            user=user,
            status=status
        )

    def created_user_and_enroll(self, enrollment_type):
        """Create and enroll users with provided enrollment type."""

        user = UserFactory.create()
        CourseEnrollment.objects.create(
            user=user,
            course_id=self.course.id,
            mode=enrollment_type,
            is_active=True
        )
        return user

    def setUp(self):
        super(UserAccessToContent, self).setUp()
        # Create the course
        self.course = CourseFactory.create(org="MIT", course="DemoX", run="CS101")

        self.section_alone = ItemFactory.create(
            parent=self.course, category='chapter', display_name='Test Alone Section'
        )

        self.section_with_tree = ItemFactory.create(
            parent=self.course, category='chapter', display_name='Test Section Tree'
        )

        self.subsection_alone = ItemFactory.create(
            parent=self.section_with_tree, category='sequential', display_name='Test Subsection No Tree'
        )

        self.subsection_with_tree = ItemFactory.create(
            parent=self.section_with_tree, category='sequential', display_name='Test Subsection With Tree'
        )

        self.icrv_parent_vertical = ItemFactory.create(
            parent=self.subsection_with_tree, category='vertical', display_name='Test Unit X Block Parent'
        )

        self.icrv_x_block = ItemFactory.create(
            parent=self.icrv_parent_vertical, category='edx-reverification-block', display_name='Test Unit X Block 1'
        )

        self.icrv_x_block_sibling_problem = ItemFactory.create(
            parent=self.icrv_parent_vertical,
            category='problem',
            display_name='Problem icrv sibling'
        )

        self.first_checkpoint = VerificationCheckpoint.objects.create(
            course_id=self.course.id,
            checkpoint_location=self.icrv_x_block.location
        )

        self.gated_vertical = ItemFactory.create(
            parent=self.subsection_with_tree,
            category='vertical',
            display_name='Vertical with gated contents 1'
        )
        self.gated_problem1 = ItemFactory.create(
            parent=self.gated_vertical,
            category='problem',
            display_name='Problem 1'
        )
        self.gated_problem2 = ItemFactory.create(
            parent=self.gated_vertical,
            category='problem',
            display_name='Problem 2'
        )

        self.gated_icrv_x_block = ItemFactory.create(
            parent=self.gated_vertical,
            category='edx-reverification-block',
            display_name='Test Unit Gated X Block 1'
        )

        self.second_checkpoint = VerificationCheckpoint.objects.create(
            course_id=self.course.id,
            checkpoint_location=self.gated_icrv_x_block.location
        )

    @ddt.data(
        ("verified", SUBMITTED),
        ("verified", APPROVED),
        ("verified", DENIED),
        ("verified", None),
        ("verified", SKIPPED),
        ("honor", None),
    )
    @ddt.unpack
    def test_has_access_for_users(self, enrollment_type, verification_status):

        on_course_publish(self.course.id)
        course = modulestore().get_course(self.course.id)

        section_alone = modulestore().get_item(self.section_alone.location)

        section_with_tree = modulestore().get_item(self.section_with_tree.location)
        subsection_alone = modulestore().get_item(self.subsection_alone.location)
        subsection_with_tree = modulestore().get_item(self.subsection_with_tree.location)

        icrv_parent_vertical = modulestore().get_item(self.icrv_parent_vertical.location)
        icrv_xblock = modulestore().get_item(self.icrv_x_block.location)
        icrv_xblock_sibling_problem = modulestore().get_item(self.icrv_x_block_sibling_problem.location)

        gated_vertical = modulestore().get_item(self.gated_vertical.location)
        gated_problem1 = modulestore().get_item(self.gated_problem1.location)
        gated_problem2 = modulestore().get_item(self.gated_problem2.location)
        gated_icrv_xblock = modulestore().get_item(self.gated_icrv_x_block.location)

        # creating user and enroll them.
        user = self.created_user_and_enroll(enrollment_type)
        if verification_status:
            self.add_verification_status(user, verification_status)

        # user is verified and but has not attempted yet, user group will
        # be VERIFIED_DENIED, denied users will have access to ICRV but
        # exam content will be hidden
        elif verification_status is None and enrollment_type == "verified":
            self.assertTrue(_has_group_access(course, user, course.id).has_access)

            self.assertTrue(_has_group_access(section_alone, user, course.id).has_access)
            self.assertTrue(_has_group_access(section_with_tree, user, course.id).has_access)

            self.assertTrue(_has_group_access(subsection_alone, user, course.id).has_access)
            self.assertTrue(_has_group_access(subsection_with_tree, user, course.id).has_access)

            self.assertTrue(_has_group_access(icrv_parent_vertical, user, course.id).has_access)
            self.assertTrue(_has_group_access(icrv_xblock, user, course.id).has_access)
            self.assertFalse(_has_group_access(icrv_xblock_sibling_problem, user, course.id).has_access)

            self.assertFalse(_has_group_access(gated_vertical, user, course.id).has_access)
            self.assertFalse(_has_group_access(gated_problem1, user, course.id).has_access)
            self.assertFalse(_has_group_access(gated_problem2, user, course.id).has_access)
            self.assertTrue(_has_group_access(gated_icrv_xblock, user, course.id).has_access)

        # user is in non-verified mode, user group will be NON_VERIFIED
        # Non verified users will have access to all content excluding ICRVs
        if enrollment_type == 'honor':
            self.assertTrue(_has_group_access(course, user, course.id).has_access)

            self.assertTrue(_has_group_access(section_alone, user, course.id).has_access)
            self.assertTrue(_has_group_access(section_with_tree, user, course.id).has_access)

            self.assertTrue(_has_group_access(subsection_alone, user, course.id).has_access)
            self.assertTrue(_has_group_access(subsection_with_tree, user, course.id).has_access)

            self.assertTrue(_has_group_access(icrv_parent_vertical, user, course.id).has_access)
            self.assertFalse(_has_group_access(icrv_xblock, user, course.id).has_access)
            self.assertTrue(_has_group_access(icrv_xblock_sibling_problem, user, course.id).has_access)

            self.assertTrue(_has_group_access(gated_vertical, user, course.id).has_access)
            self.assertTrue(_has_group_access(gated_problem1, user, course.id).has_access)
            self.assertTrue(_has_group_access(gated_problem2, user, course.id).has_access)
            self.assertFalse(_has_group_access(gated_icrv_xblock, user, course.id).has_access)

        # user has submitted, denied or approved, user group will be VERIFIED_ALLOW
        elif enrollment_type == 'verified' and \
                verification_status in [self.SUBMITTED, self.APPROVED, self.DENIED, self.SKIPPED]:
            if verification_status == self.SKIPPED:
                SkippedReverification.add_skipped_reverification_attempt(
                    checkpoint=self.first_checkpoint,
                    user_id=user.id,
                    course_id=self.course.id
                )

            # allowed users will have access to all content
            self.assertTrue(_has_group_access(course, user, course.id).has_access)

            self.assertTrue(_has_group_access(section_alone, user, course.id).has_access)
            self.assertTrue(_has_group_access(section_with_tree, user, course.id).has_access)

            self.assertTrue(_has_group_access(subsection_alone, user, course.id).has_access)
            self.assertTrue(_has_group_access(subsection_with_tree, user, course.id).has_access)

            self.assertTrue(_has_group_access(icrv_parent_vertical, user, course.id).has_access)
            self.assertTrue(_has_group_access(icrv_xblock, user, course.id).has_access)
            self.assertTrue(_has_group_access(icrv_xblock_sibling_problem, user, course.id).has_access)

            self.assertTrue(_has_group_access(gated_vertical, user, course.id).has_access)
            self.assertTrue(_has_group_access(gated_problem1, user, course.id).has_access)
            self.assertTrue(_has_group_access(gated_problem2, user, course.id).has_access)
            self.assertTrue(_has_group_access(gated_icrv_xblock, user, course.id).has_access)
