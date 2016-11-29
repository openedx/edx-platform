from cms.envs.common import *
from openedx.stanford.lms.envs.common import (
    DEFAULT_COURSE_ABOUT_IMAGE_URL,
    INSTRUCTOR_QUERY_PROBLEM_TYPES,
)

COPYRIGHT_EMAIL = 'copyright@example.com'
COURSE_UTILITIES = [
    # Todo: add aws entries for this
    {
        'short_description': 'Bulk Operations',
        'items': [
            {
                'short_description': 'Get all captions from YouTube',
                'long_description': (
                    'This utility will attempt to get or update captions for all videos '
                    'in the course from YouTube. Please allow it a couple of minutes to run.'
                ),
                'action_url': 'utility_captions_handler',
                'action_text': 'Check Captions',
                'action_external': False,
            },
            {
                'short_description': 'Bulk view problem settings',
                'long_description': (
                    'This utility will allow you to view all section, subsection '
                    'and problem settings in one page.'
                ),
                'action_url': 'utility_bulksettings_handler',
                'action_text': 'View Problem Settings',
                'action_external': False,
            },
        ],
    }
]
FEATURES.update({
    # Display option to send email confirmation of course enrollment
    'ENABLE_ENROLLMENT_EMAIL': False,

    # warning to instructors about publicly-viewable content
    'CONTENT_VISIBILITY_NOTICE': True,
})
MIDDLEWARE_CLASSES += (
    # Log out sneakpeek users
    'sneakpeek.middleware.SneakPeekLogoutMiddleware',
)
SHIB_ONLY_SITE = False
SHIB_REDIRECT_DOMAIN_WHITELIST = {}
XBLOCKS_ALWAYS_IN_STUDIO = []
