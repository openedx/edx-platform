from django.utils.translation import ugettext as _

DJANGO_COUNTRIES_INDEX = 0
DJANGO_COUNTRIES_VALUE_INDEX = 1

MARKETPLACE_PARAM_QUERY = 'query'
MARKETPLACE_PARAM_COUNTRY = 'country'
MARKETPLACE_PARAM_CITY = 'city'

ORG_PROBLEM_TYPE_DELIVERY_SERVICES = 'delivery-services'
ORG_PROBLEM_TYPE_FUNDING = 'funding'
ORG_PROBLEM_TYPE_HEALTH_CARE_SUPPLIES = 'healthcare-supplies'
ORG_PROBLEM_TYPE_HUMAN_RESOURCES = 'human-resources'
ORG_PROBLEM_TYPE_MENTORSHIP = 'mentorship'
ORG_PROBLEM_TYPE_ONLINE_TRAINING = 'online-training'
ORG_PROBLEM_TYPE_OTHER = 'other-problem'
ORG_PROBLEM_TYPE_REMOTE_WORKING_TOOLS = 'remote-working-tools'

ORG_PROBLEM_CHOICES = [
    (ORG_PROBLEM_TYPE_HEALTH_CARE_SUPPLIES, _('Healthcare Supplies')),
    (ORG_PROBLEM_TYPE_REMOTE_WORKING_TOOLS, _('Remote Working Tools')),
    (ORG_PROBLEM_TYPE_ONLINE_TRAINING, _('Online Training')),
    (ORG_PROBLEM_TYPE_DELIVERY_SERVICES, _('Delivery Services')),
    (ORG_PROBLEM_TYPE_MENTORSHIP, _('Mentorship')),
    (ORG_PROBLEM_TYPE_FUNDING, _('Funding')),
    (ORG_PROBLEM_TYPE_HUMAN_RESOURCES, _('Human Resources')),
]

ORG_PROBLEM_TEMPLATE_CHOICES = [
    (ORG_PROBLEM_TYPE_HEALTH_CARE_SUPPLIES, _('Healthcare Supplies')),
    (ORG_PROBLEM_TYPE_REMOTE_WORKING_TOOLS, _('Remote Working Tools')),
    (ORG_PROBLEM_TYPE_ONLINE_TRAINING, _('Online Training')),
    (ORG_PROBLEM_TYPE_DELIVERY_SERVICES, _('Delivery Services')),
    (ORG_PROBLEM_TYPE_MENTORSHIP, _('Mentorship')),
    (ORG_PROBLEM_TYPE_FUNDING, _('Funding')),
    (ORG_PROBLEM_TYPE_HUMAN_RESOURCES, _('Human Resources')),
    (ORG_PROBLEM_TYPE_OTHER, _('Other'))
]


ORG_SECTOR_HEALTH_AND_WELL_BEING = 'health-and-well-being'
ORG_SECTOR_EDUCATION = 'education'
ORG_SECTOR_GENDER_EQUALITY = 'gender-equality'
ORG_SECTOR_SANITATION = 'sanitation'
ORG_SECTOR_CLIMATE_CHANGES = 'climate-changes'
ORG_SECTOR_CLEAN_ENERGY = 'clean-energy'
ORG_SECTOR_ENVIRONMENTAL_CONSERVATION = 'environmental-conservation'
ORG_SECTOR_WORK_AND_ECONOMIC_GROWTH = 'work-and-economic-growth'
ORG_SECTOR_HUMAN_RIGHTS = 'human-rights'
ORG_SECTOR_SOCIAL_JUSTICE = 'social-justice'
ORG_SECTOR_ART_AND_CULTURE = 'art-and-culture'
ORG_SECTOR_OTHER = 'other-sector'

ORG_SECTOR_CHOICES = [
    (ORG_SECTOR_HEALTH_AND_WELL_BEING, _('Health & Well-being')),
    (ORG_SECTOR_EDUCATION, _('Education')),
    (ORG_SECTOR_GENDER_EQUALITY, _('Gender Equality')),
    (ORG_SECTOR_SANITATION, _('Sanitation')),
    (ORG_SECTOR_CLIMATE_CHANGES, _('Climate Change')),
    (ORG_SECTOR_CLEAN_ENERGY, _('Clean Energy')),
    (ORG_SECTOR_ENVIRONMENTAL_CONSERVATION, _('Environmental Conservation')),
    (ORG_SECTOR_WORK_AND_ECONOMIC_GROWTH, _('Work & Economic Growth')),
    (ORG_SECTOR_HUMAN_RIGHTS, _('Human Rights')),
    (ORG_SECTOR_SOCIAL_JUSTICE, _('Social Justice')),
    (ORG_SECTOR_ART_AND_CULTURE, _('Art & Culture'))
]


ORG_SECTOR_TEMPLATE_CHOICES = [
    (ORG_SECTOR_HEALTH_AND_WELL_BEING, _('Health & Well-being')),
    (ORG_SECTOR_EDUCATION, _('Education')),
    (ORG_SECTOR_GENDER_EQUALITY, _('Gender Equality')),
    (ORG_SECTOR_SANITATION, _('Sanitation')),
    (ORG_SECTOR_CLIMATE_CHANGES, _('Climate Change')),
    (ORG_SECTOR_CLEAN_ENERGY, _('Clean Energy')),
    (ORG_SECTOR_ENVIRONMENTAL_CONSERVATION, _('Environmental Conservation')),
    (ORG_SECTOR_WORK_AND_ECONOMIC_GROWTH, _('Work & Economic Growth')),
    (ORG_SECTOR_HUMAN_RIGHTS, _('Human Rights')),
    (ORG_SECTOR_SOCIAL_JUSTICE, _('Social Justice')),
    (ORG_SECTOR_ART_AND_CULTURE, _('Art & Culture')),
    (ORG_SECTOR_OTHER, _('Other'))
]

USER_SERVICES_DELIVERY_SERVICES = 'delivery-services'
USER_SERVICES_FUNDING = 'funding'
USER_SERVICES_HEALTH_CARE_SUPPLIES = 'healthcare-supplies'
USER_SERVICES_MENTORSHIP = 'mentorship'
USER_SERVICES_ONLINE_TRAINING = 'online-training'
USER_SERVICES_PEOPLE_POWER = 'people-power'

USER_SERVICES_CHOICES = (
    (USER_SERVICES_HEALTH_CARE_SUPPLIES, _('Healthcare Supplies')),
    (USER_SERVICES_PEOPLE_POWER, _('People Power')),
    (USER_SERVICES_ONLINE_TRAINING, _('Online Training')),
    (USER_SERVICES_DELIVERY_SERVICES, _('Delivery Services')),
    (USER_SERVICES_MENTORSHIP, _('Mentorship')),
    (USER_SERVICES_FUNDING, _('Funding')),
)

PUBLISHED_DATE_FORMAT = '%B %d, %Y'
