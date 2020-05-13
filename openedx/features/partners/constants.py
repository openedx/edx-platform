# Partner extended profile keys
ENGLISH_PROFICIENCY_KEY = 'english_proficiency'
GENDER_KEY = 'gender'
HOURS_PER_WEEK_KEY = 'hours_per_week'
IS_FIRST_LEARNER = 'is_first_learner'
IS_INTERESTS_DATA_SUBMITTED_KEY = 'is_interests_data_submitted'
IS_ORGANIZATION_METRICS_SUBMITTED = 'is_organization_metrics_submitted'
LANGUAGE_KEY = 'language'
LEVEL_OF_EDUCATION_KEY = 'level_of_education'
ORGANIZATION_NAME_KEY = 'organization_name'
ROLE_IN_ORG_KEY = 'role_in_org'
YEAR_OF_BIRTH_KEY = 'year_of_birth'

# Partner organization keys
COUNTRY_KEY = 'country'
FOCUS_AREA_KEY = 'focus_area'
FOUNDING_YEAR_KEY = 'founding_year'
LEVEL_OF_OPERATION_KEY = 'level_of_operation'
ORG_TYPE_KEY = 'org_type'
START_MONTH_YEAR_KEY = 'start_month_year'
TOTAL_EMPLOYEES_KEY = 'total_employees'

OPT_IN_DATA = 'no'  # By default user opt out of emails by MailChimp

# These are minimum required fields to complete registration
# These are the default values for Give2Asia partner
PARTNER_EXTENDED_PROFILE_DEFAULT_DATA = {
    ENGLISH_PROFICIENCY_KEY: 'IWRNS',  # I'd rather not say
    HOURS_PER_WEEK_KEY: 1,
    IS_INTERESTS_DATA_SUBMITTED_KEY: True,  # Flag required for by-passing interests form
    ROLE_IN_ORG_KEY: 'IWRNS',  # I'd rather not say
}

PARTNER_USER_PROFILE_DEFAULT_DATA = {
    GENDER_KEY: 'o', # I'd rather not say
    LANGUAGE_KEY: 'English',
    LEVEL_OF_EDUCATION_KEY: 'IWRNS',  # I'd rather not say
    YEAR_OF_BIRTH_KEY: 1900,
}

# Minimum required fields for making user first learner of an organization
# when he register from Give2Asia (partner) flow
PARTNER_ORGANIZATION_DEFAULT_DATA = {
    FOCUS_AREA_KEY: 'IWRNS',  # I'd rather not say
    FOUNDING_YEAR_KEY: '0',  # set to zero
    LEVEL_OF_OPERATION_KEY: 'IWRNS',  # I'd rather not say
    TOTAL_EMPLOYEES_KEY: 'NOTAPP',  # Not Applicable
}

PERFORMANCE_PERM_FRMT = 'can_access_{slug}_performance'

PARTNER_USER_STATUS_WAITING = 'waiting'
PARTNER_USER_STATUS_APPROVED = 'approved'

PARTNERS_TOP_REGISTRATION_COUNTRIES = {
    'give2asia': (
        ('NG', 'Nigeria'),
        ('IN', 'India'),
        ('PK', 'Pakistan'),
        ('KE', 'Kenya'),
        ('GH', 'Ghana'),
    )
}
