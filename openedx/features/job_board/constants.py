JOB_PARAM_QUERY_KEY = 'query'
JOB_PARAM_COUNTRY_KEY = 'country'
JOB_PARAM_CITY_KEY = 'city'

JOB_TYPE_REMOTE_INDEX = 0
JOB_TYPE_ONSITE_INDEX = 1

JOB_TYPE_CHOICES = (
    ('remote', 'Remote'),
    ('onsite', 'Onsite'),
)

JOB_HOURS_FULLTIME_INDEX = 0
JOB_HOURS_PARTTIME_INDEX = 1
JOB_HOURS_FREELANCE_INDEX = 2

JOB_COMPENSATION_CHOICES = (
    ('volunteer', 'Volunteer'),
    ('hourly', 'Hourly'),
    ('salaried', 'Salaried'),
)

JOB_COMP_VOLUNTEER_INDEX = 0
JOB_COMP_HOURLY_INDEX = 1
JOB_COMP_SALARIED_INDEX = 2

JOB_HOURS_CHOICES = (
    ('fulltime', 'Full Time'),
    ('parttime', 'Part Time'),
    ('freelance', 'Freelance'),
)

JOB_TUPLE_KEY_INDEX = 0
DJANGO_COUNTRIES_KEY_INDEX = 0
DJANGO_COUNTRIES_VALUE_INDEX = 1
