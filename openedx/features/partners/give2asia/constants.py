ORGANIZATION_NAME_KEY = 'organization_name'
ENGLISH_PROFICIENCY_KEY = 'english_proficiency'
START_MONTH_YEAR_KEY = 'start_month_year'
IS_INTERESTS_DATA_SUBMITTED_KEY = 'is_interests_data_submitted'
FIRST_NAME_KEY = 'first_name'
LAST_NAME_KEY = 'last_name'
YEAR_OF_BIRTH_KEY = 'year_of_birth'
LEVEL_OF_EDUCATION_KEY = 'level_of_education'
OPT_IN_KEY = 'opt_in'
# These are minimum required fields to complete registration
# These are the default values for Give2Asia partner
GIVE2ASIA_DEFAULT_DATA = {
    YEAR_OF_BIRTH_KEY: 2000,
    LEVEL_OF_EDUCATION_KEY: 'IWRNS',  # set I'd rather not say for education level
    ENGLISH_PROFICIENCY_KEY: 'IWRNS',  # set I'd rather not say for english proficiency
    START_MONTH_YEAR_KEY: '11/2019',
    IS_INTERESTS_DATA_SUBMITTED_KEY: True,  # Flag required for by-passing interests form
    OPT_IN_KEY: 'no'  # By default user opt out of emails by MailChimp
}
