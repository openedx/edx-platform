"""
Mocked data for specializations app tests
"""


def mock_get_program(courses=None):
    if courses is None:
        courses = []
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
