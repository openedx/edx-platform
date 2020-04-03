from datetime import datetime, timedelta

from openedx.features.specializations.helpers import DISCOVERY_DATE_FORMAT


def mock_get_program(courses=[]):
    return {
        'uuid': 'eb228773-a9a5-48cf-bb0e-94725d5aa4f1',
        'title': 'Specialization',
        'subtitle': 'This is management specialization',
        'type': 'Professional Certificate',
        'status': 'active',
        'marketing_slug': 'discovery-specialization-1',
        'marketing_url': 'professional-certificate/discovery-specialization-1',
        'banner_image': {
            'x-small': {
                'url': 'http://localhost:18381/media/media/programs/banner_images/eb228773-a9a5-48cf-bb0e'
                       '-94725d5aa4f1-c147bfda9f30.x-small.jpg',
                'width': 348,
                'height': 116
            },
            'large': {
                'url': 'http://localhost:18381/media/media/programs/banner_images/eb228773-a9a5-48cf-bb0e'
                       '-94725d5aa4f1-c147bfda9f30.large.jpg',
                'width': 1440,
                'height': 480
            },
            'small': {
                'url': 'http://localhost:18381/media/media/programs/banner_images/eb228773-a9a5-48cf-bb0e'
                       '-94725d5aa4f1-c147bfda9f30.small.jpg',
                'width': 435,
                'height': 145
            },
            'medium': {
                'url': 'http://localhost:18381/media/media/programs/banner_images/eb228773-a9a5-48cf-bb0e'
                       '-94725d5aa4f1-c147bfda9f30.medium.jpg',
                'width': 726,
                'height': 242
            }
        },
        'hidden': False,
        'courses': courses,
        'authoring_organizations': [],
        'card_image_url': None,
        'is_program_eligible_for_one_click_purchase': True,
        'degree': None,
        'overview': '<h1>Specialization About page</h1>',
        'total_hours_of_effort': None,
        'weeks_to_complete': None,
        'weeks_to_complete_min': None,
        'weeks_to_complete_max': None,
        'min_hours_effort_per_week': None,
        'max_hours_effort_per_week': None,
        'video': None,
        'expected_learning_items': [],
        'faq': [],
        'credit_backing_organizations': [],
        'corporate_endorsements': [],
        'job_outlook_items': [],
        'individual_endorsements': [],
        'languages': [],
        'transcript_languages': [],
        'subjects': [],
        'price_ranges': [],
        'staff': [],
        'credit_redemption_overview': '',
        'applicable_seat_types': [
            'verified',
            'professional',
            'credit',
            'audit'
        ],
        'instructor_ordering': [],
        'enrollment_count': 0,
        'recent_enrollment_count': 0,
        'topics': []
    }


def mock_course(course_runs=[]):
    return {
        'key': 'Arbisoft+TCA102',
        'uuid': 'c8b485e5-20a2-41c2-a089-513cb8ef3952',
        'title': 'Test Cousrse',
        'course_runs': course_runs,
        'entitlements': [],
        'owners': [
            {
                'uuid': 'd69cbadd-dd82-4553-8cde-28be4a6d26d0',
                'key': 'Arbisoft',
                'name': ''
            }
        ],
        'image': None,
        'short_description': None
    }


def mock_course_run(enrollment_start, enrollment_end):
    return {
        'key': 'course-v1:Arbisoft+TCA102+2019_T2',
        'uuid': '3de0a590-5013-4e9c-8861-bd37e48ddff2',
        'title': 'Test Competency Assessment',
        'image': None,
        'short_description': 'This is test course',
        'marketing_url': 'course/test-competency-assessment?utm_medium=affiliate_partner&utm_source=edx',
        'seats': [],
        'start': '2019-12-01T00:00:00Z',
        'end': '2020-12-31T00:00:00Z',
        'enrollment_start': enrollment_start.strftime(DISCOVERY_DATE_FORMAT) if enrollment_start else None,
        'enrollment_end': enrollment_end.strftime(DISCOVERY_DATE_FORMAT) if enrollment_end else None,
        'pacing_type': 'instructor_paced',
        'type': None,
        'status': 'published'
    }


def mock_get_program_with_open_course_runs():
    now = datetime.now()
    enrollment_start = now - timedelta(days=10)
    enrollment_end = now + timedelta(days=10)

    course_run = mock_course_run(enrollment_start, enrollment_end)
    course = mock_course([course_run])
    return mock_get_program([course])


def mock_get_program_with_closed_course_runs():
    now = datetime.now()

    past_enrollment_start = now - timedelta(days=20)
    past_enrollment_end = now - timedelta(days=10)
    past_course_run = mock_course_run(past_enrollment_start, past_enrollment_end)
    past_course = mock_course([past_course_run])

    return mock_get_program([past_course])


def mock_get_program_with_future_course_runs():
    now = datetime.now()

    future_enrollment_start = now + timedelta(days=10)
    future_enrollment_end = now + timedelta(days=20)
    future_course_run = mock_course_run(future_enrollment_start, future_enrollment_end)
    future_course = mock_course([future_course_run])

    return mock_get_program([future_course])


def mock_get_program_with_runs_having_no_dates():
    course_run = mock_course_run(None, None)
    course = mock_course([course_run])

    return mock_get_program([course])
