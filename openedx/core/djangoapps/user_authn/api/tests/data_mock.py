"""
Constants for testing MFE Context API
"""

_tpa_providers = [
    {
        'id': 'oa2-facebook',
        'name': 'Facebook',
        'iconClass': 'fa-facebook',
        'iconImage': None,
        'skipHintedLogin': False,
        'skipRegistrationForm': False,
        'loginUrl': 'https://facebook.com/login',
        'registerUrl': 'https://facebook.com/register'
    },
    {
        'id': 'oa2-google-oauth2',
        'name': 'Google',
        'iconClass': 'fa-google-plus',
        'iconImage': None,
        'skipHintedLogin': False,
        'skipRegistrationForm': False,
        'loginUrl': 'https://google.com/login',
        'registerUrl': 'https://google.com/register'
    }
]

MFE_CONTEXT_WITH_TPA_DATA = {
    'context_data': {
        'currentProvider': 'edX',
        'platformName': 'edX',
        'providers': _tpa_providers,
        'secondaryProviders': [],
        'finishAuthUrl': 'https://edx.com/auth/finish',
        'errorMessage': None,
        'registerFormSubmitButtonText': 'Create Account',
        'autoSubmitRegForm': False,
        'syncLearnerProfileData': False,
        'countryCode': '',
        'pipeline_user_details': {
            'username': 'test123',
            'email': 'test123@edx.com',
            'fullname': 'Test Test',
            'first_name': 'Test',
            'last_name': 'Test'
        }
    },
}

SERIALIZED_MFE_CONTEXT_WITH_TPA_DATA = {
    'contextData': {
        'currentProvider': 'edX',
        'platformName': 'edX',
        'providers': _tpa_providers,
        'secondaryProviders': [],
        'finishAuthUrl': 'https://edx.com/auth/finish',
        'errorMessage': None,
        'registerFormSubmitButtonText': 'Create Account',
        'autoSubmitRegForm': False,
        'syncLearnerProfileData': False,
        'countryCode': '',
        'pipelineUserDetails': {
            'username': 'test123',
            'email': 'test123@edx.com',
            'name': 'Test Test',
            'firstName': 'Test',
            'lastName': 'Test'
        }
    },
    'registrationFields': {},
    'optionalFields': {
        'extended_profile': []
    }
}

MFE_CONTEXT_WITHOUT_TPA_DATA = {
    'context_data': {
        'currentProvider': None,
        'platformName': 'édX',
        'providers': [],
        'secondaryProviders': [],
        'finishAuthUrl': None,
        'errorMessage': None,
        'registerFormSubmitButtonText': 'Create Account',
        'autoSubmitRegForm': False,
        'syncLearnerProfileData': False,
        'countryCode': '',
        'pipeline_user_details': {}
    }
}

SERIALIZED_MFE_CONTEXT_WITHOUT_TPA_DATA = {
    'contextData': {
        'currentProvider': None,
        'platformName': 'édX',
        'providers': [],
        'secondaryProviders': [],
        'finishAuthUrl': None,
        'errorMessage': None,
        'registerFormSubmitButtonText': 'Create Account',
        'autoSubmitRegForm': False,
        'syncLearnerProfileData': False,
        'countryCode': '',
        'pipelineUserDetails': {}
    },
    'registrationFields': {},
    'optionalFields': {
        'extended_profile': []
    }
}
