"""
Tests certain functions in courseware toggles.py
"""
from unittest import TestCase

import ddt
from django.test.utils import override_settings

from opaque_keys.edx.keys import CourseKey

from ..toggles import courseware_legacy_is_visible, courseware_mfe_is_visible


@ddt.ddt
class TestIsVisible(TestCase):
    """
    Test toggles related to MFE/Legacy courseware visibility.

    This is controlled entirely through Django settings
    (with the exception that Old Mongo courses are only ever visible
    in the Legacy experience, as long as they remain in the platform).

    There are two sets of settings we care about:

    Course Micro-Frontend Settings:
    * LEARNING_MICROFRONTEND_ENABLED
    * LEARNING_MICROFRONTEND_INCLUSIONS
    * LEARNING_MICROFRONTEND_EXCLUSIONS
    These determine which experience is active for learners.
    Learners can only ever see that experience; they are not allowed
    to flip back and forth.

    Course Micro-Frontend Educator Preview Settings:
    * LEARNING_MICROFRONTEND_PREVIEW_ENABLED
    * LEARNING_MICROFRONTEND_PREVIEW_INCLUSIONS
    * LEARNING_MICROFRONTEND_PREVIEW_EXCLUSIONS
    These determine whether course staff is permitted to view the inactive
    experience (that is, view Legacy courseware when the MFE is enabled,
    or vice versa).

    Global staff are always permitted to view either experience
    (except, again, in the case of Old Mongo coures, which only render in Legacy).
    """

    new_course_id = "course-v1:OpenEdX+New+2020"
    old_mongo_course_id = "OpenEdX/Old/2020"

    @ddt.data(
        # With default settings: course is only visible in MFE,
        # except to global staff, which can still see it in Legacy.
        {
            'course_id': new_course_id,
            'settings': {},
            'expect_mfe_visible_for_learners': True,
            'expect_mfe_visible_for_course_staff': True,
            'expect_mfe_visible_for_global_staff': True,
            'expect_legacy_visible_for_learners': False,
            'expect_legacy_visible_for_course_staff': False,
            'expect_legacy_visible_for_global_staff': True,
        },
        # MFE can be disabled for a single course.
        {
            'course_id': new_course_id,
            'settings': {
                'LEARNING_MICROFRONTEND_EXCLUSIONS': [new_course_id],
            },
            'expect_mfe_visible_for_learners': False,
            'expect_mfe_visible_for_course_staff': False,
            'expect_mfe_visible_for_global_staff': True,
            'expect_legacy_visible_for_learners': True,
            'expect_legacy_visible_for_course_staff': True,
            'expect_legacy_visible_for_global_staff': True,
        },
        # MFE can be disabled for a single course,
        # with the educator preview then enabled for that course,
        # thus granting course staff access to the MFE.
        {
            'course_id': new_course_id,
            'settings': {
                'LEARNING_MICROFRONTEND_EXCLUSIONS': [new_course_id],
                'LEARNING_MICROFRONTEND_PREVIEW_INCLUSIONS': [new_course_id],
            },
            'expect_mfe_visible_for_learners': False,
            'expect_mfe_visible_for_course_staff': True,
            'expect_mfe_visible_for_global_staff': True,
            'expect_legacy_visible_for_learners': True,
            'expect_legacy_visible_for_course_staff': True,
            'expect_legacy_visible_for_global_staff': True,
        },
        # MFE can be globally disabled.
        # Global staff (and only global staff) can use MFE.
        {
            'course_id': new_course_id,
            'settings': {
                'LEARNING_MICROFRONTEND_ENABLED': False,
            },
            'expect_mfe_visible_for_learners': False,
            'expect_mfe_visible_for_course_staff': False,
            'expect_mfe_visible_for_global_staff': True,
            'expect_legacy_visible_for_learners': True,
            'expect_legacy_visible_for_course_staff': True,
            'expect_legacy_visible_for_global_staff': True,
        },
        # MFE can be globally disabled, but the educator preview globally enabled.
        # Both global and course staff can use the MFE.
        {
            'course_id': new_course_id,
            'settings': {
                'LEARNING_MICROFRONTEND_ENABLED': False,
                'LEARNING_MICROFRONTEND_PREVIEW_ENABLED': True,
            },
            'expect_mfe_visible_for_learners': False,
            'expect_mfe_visible_for_course_staff': True,
            'expect_mfe_visible_for_global_staff': True,
            'expect_legacy_visible_for_learners': True,
            'expect_legacy_visible_for_course_staff': True,
            'expect_legacy_visible_for_global_staff': True,
        },
        # Somewhat complex case:
        # MFE is globally disabled, but enabled for a course.
        # The educator preview is globally enabled, but disabled for course.
        # The result: Learners and course staff can only see the MFE.
        {
            'course_id': new_course_id,
            'settings': {
                'LEARNING_MICROFRONTEND_ENABLED': False,
                'LEARNING_MICROFRONTEND_INCLUSIONS': [new_course_id],
                'LEARNING_MICROFRONTEND_PREVIEW_ENABLED': True,
                'LEARNING_MICROFRONTEND_PREVIEW_EXCLUSIONS': [new_course_id],
            },
            'expect_mfe_visible_for_learners': True,
            'expect_mfe_visible_for_course_staff': True,
            'expect_mfe_visible_for_global_staff': True,
            'expect_legacy_visible_for_learners': False,
            'expect_legacy_visible_for_course_staff': False,
            'expect_legacy_visible_for_global_staff': True,
        },
        # No matter how much we try to enable an old mongo course,
        # only the legacy experience will ever be visible for it.
        {
            'course_id': old_mongo_course_id,
            'settings': {
                'LEARNING_MICROFRONTEND_ENABLED': True,
                'LEARNING_MICROFRONTEND_INCLUDE': [old_mongo_course_id],
                'LEARNING_MICROFRONTEND_PREIVEW_ENABLED': True,
                'LEARNING_MICROFRONTEND_PREIVEW_INCLUDE': [old_mongo_course_id],
            },
            'expect_mfe_visible_for_learners': False,
            'expect_mfe_visible_for_course_staff': False,
            'expect_mfe_visible_for_global_staff': False,
            'expect_legacy_visible_for_learners': True,
            'expect_legacy_visible_for_course_staff': True,
            'expect_legacy_visible_for_global_staff': True,
        },
    )
    @ddt.unpack
    def test_courseware_visiblity(
            self,
            course_id,
            settings,
            expect_mfe_visible_for_learners,
            expect_mfe_visible_for_course_staff,
            expect_mfe_visible_for_global_staff,
            expect_legacy_visible_for_learners,
            expect_legacy_visible_for_course_staff,
            expect_legacy_visible_for_global_staff,
    ):
        course_key = CourseKey.from_string(course_id)

        with override_settings(**settings):

            assert courseware_mfe_is_visible(
                course_key
            ) is expect_mfe_visible_for_learners

            assert courseware_mfe_is_visible(
                course_key, is_course_staff=True
            ) is expect_mfe_visible_for_course_staff

            assert courseware_mfe_is_visible(
                course_key, is_global_staff=True
            ) is expect_mfe_visible_for_global_staff

            assert courseware_legacy_is_visible(
                course_key
            ) is expect_legacy_visible_for_learners

            assert courseware_legacy_is_visible(
                course_key, is_course_staff=True
            ) is expect_legacy_visible_for_course_staff

            assert courseware_legacy_is_visible(
                course_key, is_global_staff=True
            ) is expect_legacy_visible_for_global_staff
