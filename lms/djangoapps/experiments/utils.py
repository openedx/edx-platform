"""
Utilities to facilitate experimentation
"""

import json
from student.models import CourseEnrollment
from django_comment_common.models import Role
from course_modes.models import get_cosmetic_verified_display_price
from courseware.access import has_staff_access_to_preview_mode
from courseware.date_summary import verified_upgrade_deadline_link, verified_upgrade_link_is_valid
from xmodule.partitions.partitions_service import get_user_partition_groups, get_all_partitions_for_course
from opaque_keys.edx.keys import CourseKey


def check_and_get_upgrade_link_and_date(user, enrollment=None, course=None):
    """
    For an authenticated user, return a link to allow them to upgrade
    in the specified course.

    Returns the upgrade link and upgrade deadline for a user in a given course given
    that the user is within the window to upgrade defined by our dynamic pacing feature;
    otherwise, returns None for both the link and date.
    """
    if enrollment is None and course is None:
        raise ValueError("Must specify either an enrollment or a course")

    if enrollment:
        if course is None:
            course = enrollment.course
        elif enrollment.course_id != course.id:
            raise ValueError("{} refers to a different course than {} which was supplied".format(
                enrollment, course
            ))

        if enrollment.user_id != user.id:
            raise ValueError("{} refers to a different user than {} which was supplied".format(
                enrollment, user
            ))

    if enrollment is None:
        enrollment = CourseEnrollment.get_enrollment(user, course.id)

    if user.is_authenticated and verified_upgrade_link_is_valid(enrollment):
        return (
            verified_upgrade_deadline_link(user, course),
            enrollment.upgrade_deadline
        )

    return (None, None)


# TODO: clean up as part of REVEM-198 (START)
def get_mock_programs():
    """
    Return mock program results. This mimics the results from
    openedx.core.djangoapps.catalog.utils.get_programs(course=course.id)
    """
    # pylint: disable=unicode-format-string
    mock_programs_str = '[{"is_program_eligible_for_one_click_purchase": true, "subtitle": "", ' \
                        '"recent_enrollment_count": 0, "overview": "A demo program for testing.", ' \
                        '"total_hours_of_effort": 4, "weeks_to_complete": null, "corporate_endorsements": [], ' \
                        '"video": null, "type": "MicroMasters", "applicable_seat_types": ["verified", ' \
                        '"professional", "credit"], "max_hours_effort_per_week": 4, "transcript_languages": [], ' \
                        '"staff": [], "uuid": "c7568949-1ced-4f05-87ef-0d27e2f3e846", "title": ' \
                        '"edX Demonstration Program", "languages": [], "subjects": [], "individual_endorsements": ' \
                        '[], "hidden": false, "expected_learning_items": [], "marketing_slug": "demo-program", ' \
                        '"topics": [], "marketing_url": "micromasters/demo-program", "status": "active", ' \
                        '"credit_redemption_overview": null, "card_image_url": ' \
                        '"http://edx.devstack.lms:18000/asset-v1:edX+DemoX+Demo_Course+type@asset+block@' \
                        'images_course_image.jpg", "degree": null, "faq": [], "price_ranges": [{"currency": "USD", ' \
                        '"total": 149.0, "min": 149.0, "max": 149.0}], "banner_image": {"large": {"url": ' \
                        '"http://localhost:18381/media/media/programs/banner_images/' \
                        'c7568949-1ced-4f05-87ef-0d27e2f3e846-222f48c5d69c.large.jpg", "width": 1440, "height": ' \
                        '480}, "small": {"url": ' \
                        '"http://localhost:18381/media/media/programs/banner_images/' \
                        'c7568949-1ced-4f05-87ef-0d27e2f3e846-222f48c5d69c.small.jpg", "width": 435, "height": 145}, ' \
                        '"medium": {"url": ' \
                        '"http://localhost:18381/media/media/programs/banner_images/' \
                        'c7568949-1ced-4f05-87ef-0d27e2f3e846-222f48c5d69c.medium.jpg", "width": 726, "height": 242},' \
                        ' "x-small": {"url": ' \
                        '"http://localhost:18381/media/media/programs/banner_images/' \
                        'c7568949-1ced-4f05-87ef-0d27e2f3e846-222f48c5d69c.x-small.jpg", "width": 348, "height": ' \
                        '116}}, "curricula": [], "authoring_organizations": [{"logo_image_url": null, "description":' \
                        ' null, "tags": [], "uuid": "a66dece0-328b-4034-ac53-e26ff19cb295", "homepage_url": null, ' \
                        '"key": "edX", "certificate_logo_image_url": null, "marketing_url": null, "name": ""}], ' \
                        '"pathway_ids": [], "job_outlook_items": [], "credit_backing_organizations": ' \
                        '[{"logo_image_url": null, "description": null, "tags": [], "uuid": ' \
                        '"a66dece0-328b-4034-ac53-e26ff19cb295", "homepage_url": null, "key": "edX", ' \
                        '"certificate_logo_image_url": null, "marketing_url": null, "name": ""}], ' \
                        '"min_hours_effort_per_week": 1, "courses": [{"owners": [{"uuid":' \
                        ' "a66dece0-328b-4034-ac53-e26ff19cb295", "key": "edX", "name": ""}],' \
                        ' "uuid": "37596243-f7c8-4d19-a85d-c0f4b5242254", "title": "edX Demonstration Course", ' \
                        '"image": {"width": null, "height": null, "description": null, "src": ' \
                        '"http://edx.devstack.lms:18000/asset-v1:edX+DemoX+Demo_Course+type@asset+block@' \
                        'images_course_image.jpg"}, "entitlements": [], "key": "edX+DemoX", "short_description": ' \
                        'null, "course_runs": [{"status": "published", "end": null, "uuid": ' \
                        '"abc34cf9-0b33-4d04-b58a-f0f60fba9b0d", "title": "edX Demonstration Course", "image": ' \
                        '{"width": null, "height": null, "description": null, "src": ' \
                        '"http://edx.devstack.lms:18000/asset-v1:edX+DemoX+Demo_Course+type@asset+block@' \
                        'images_course_image.jpg"}, "enrollment_start": null, "start": "2013-02-05T05:00:00Z", ' \
                        '"short_description": null, "pacing_type": "instructor_paced", "key": ' \
                        '"course-v1:edX+DemoX+Demo_Course", "seats": [{"sku": "8CF08E5", "credit_hours": null, ' \
                        '"price": "149.00", "currency": "USD", "bulk_sku": "A5B6DBE", "upgrade_deadline": ' \
                        '"2020-02-21T20:29:27.181115Z", "credit_provider": null, "type": "verified"}, {"sku": ' \
                        '"68EFFFF", "credit_hours": null, "price": "0.00", "currency": "USD", "bulk_sku": null, ' \
                        '"upgrade_deadline": null, "credit_provider": null, "type": "audit"}], "enrollment_end": ' \
                        'null, "type": "verified", "marketing_url": null}]}], "weeks_to_complete_max": null, ' \
                        '"instructor_ordering": [], "enrollment_count": 0, "weeks_to_complete_min": null}]'
    return json.loads(mock_programs_str)
# TODO: clean up as part of REVEM-198 (END)


# TODO: clean up as part of REVEM-199 (START)
def is_enrolled_in_all_courses_in_program(courses_in_program, user_enrollments):
    """
    Determine if the user is enrolled in all courses in this program
    """
    # Get the enrollment course ids here, so we don't need to loop through them for every course run
    enrollment_course_ids = {enrollment.course_id for enrollment in user_enrollments}

    for course in courses_in_program:
        if not is_enrolled_in_course(course, enrollment_course_ids):
            # User is not enrolled in this course, meaning they are not enrolled in all courses in the program
            return False
    # User is enrolled in all courses in the program
    return True


def is_enrolled_in_course(course, enrollment_course_ids):
    """
    Determine if the user is enrolled in this course
    """
    course_runs = course.get('course_runs')
    if course_runs:
        for course_run in course_runs:
            if is_enrolled_in_course_run(course_run, enrollment_course_ids):
                return True
    return False


def is_enrolled_in_course_run(course_run, enrollment_course_ids):
    """
    Determine if the user is enrolled in this course run
    """
    course_run_key = CourseKey.from_string(course_run.get('key'))
    return course_run_key in enrollment_course_ids
# TODO: clean up as part of REVEM-199 (END)


def get_experiment_user_metadata_context(course, user):
    """
    Return a context dictionary with the keys used by the user_metadata.html.
    """
    enrollment_mode = None
    enrollment_time = None
    enrollment = None
    # TODO: clean up as part of REVO-28 (START)
    has_non_audit_enrollments = None
    # TODO: clean up as part of REVO-28 (END)
    # TODO: clean up as part of REVEM-199 (START)
    program_key = None
    # TODO: clean up as part of REVEM-199 (END)
    try:
        # TODO: clean up as part of REVO-28 (START)
        user_enrollments = CourseEnrollment.objects.select_related('course').filter(user_id=user.id)
        audit_enrollments = user_enrollments.filter(mode='audit')
        has_non_audit_enrollments = (len(audit_enrollments) != len(user_enrollments))
        # TODO: clean up as part of REVO-28 (END)
        enrollment = CourseEnrollment.objects.select_related(
            'course'
        ).get(user_id=user.id, course_id=course.id)
        if enrollment.is_active:
            enrollment_mode = enrollment.mode
            enrollment_time = enrollment.created

            # TODO: clean up as part of REVEM-199 (START)
            # TODO: Once openedx.core.djangoapps.catalog.utils.get_programs(course=course.id) is available, use that
            # instead. See REVEM-198.
            programs = get_mock_programs()
            if programs:
                # A course can be in multiple programs, but we're just grabbing the first one
                program = programs[0]
                complete_enrollment = False
                total_courses = None
                courses = program.get('courses')
                if courses is not None:
                    total_courses = len(courses)
                    complete_enrollment = is_enrolled_in_all_courses_in_program(courses, user_enrollments)

                program_key = {
                    'uuid': program.get('uuid'),
                    'title': program.get('title'),
                    'marketing_url': program.get('marketing_url'),
                    'total_courses': total_courses,
                    'complete_enrollment': complete_enrollment,
                }
            # TODO: clean up as part of REVEM-199 (END)
    except CourseEnrollment.DoesNotExist:
        pass  # Not enrolled, used the default None values

    # upgrade_link and upgrade_date should be None if user has passed their dynamic pacing deadline.
    upgrade_link, upgrade_date = check_and_get_upgrade_link_and_date(user, enrollment, course)
    has_staff_access = has_staff_access_to_preview_mode(user, course.id)
    forum_roles = []
    if user.is_authenticated:
        forum_roles = list(Role.objects.filter(users=user, course_id=course.id).values_list('name').distinct())

    # get user partition data
    if user.is_authenticated():
        partition_groups = get_all_partitions_for_course(course)
        user_partitions = get_user_partition_groups(course.id, partition_groups, user, 'name')
    else:
        user_partitions = {}

    return {
        'upgrade_link': upgrade_link,
        'upgrade_price': str(get_cosmetic_verified_display_price(course)),
        'enrollment_mode': enrollment_mode,
        'enrollment_time': enrollment_time,
        'pacing_type': 'self_paced' if course.self_paced else 'instructor_paced',
        'upgrade_deadline': upgrade_date,
        'course_key': course.id,
        'course_start': course.start,
        'course_end': course.end,
        'has_staff_access': has_staff_access,
        'forum_roles': forum_roles,
        'partition_groups': user_partitions,
        # TODO: clean up as part of REVO-28 (START)
        'has_non_audit_enrollments': has_non_audit_enrollments,
        # TODO: clean up as part of REVO-28 (END)
        # TODO: clean up as part of REVEM-199 (START)
        'program_key_fields': program_key,
        # TODO: clean up as part of REVEM-199 (END)
    }
