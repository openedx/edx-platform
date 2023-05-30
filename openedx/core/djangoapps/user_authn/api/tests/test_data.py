""" Mocked data for testing """

mfe_context_data_keys = {
    'contextData',
    'registrationFields',
    'optionalFields'
}

mock_mfe_context_data = {
    'context_data': {
        'currentProvider': 'edX',
        'platformName': 'edX',
        'providers': [
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
        ],
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
    'registration_fields': {},
    'optional_fields': {
        'extended_profile': []
    }
}

mock_default_mfe_context_data = {
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
    },
    'registration_fields': {},
    'optional_fields': {
        'extended_profile': []
    }
}

expected_mfe_context_data = {
    'contextData': {
        'currentProvider': 'edX',
        'platformName': 'edX',
        'providers': [
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
        ],
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

default_expected_mfe_context_data = {
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
