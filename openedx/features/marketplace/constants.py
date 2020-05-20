from django.utils.translation import ugettext as _

ORGANIZATION_SECTOR_CHOICES = (
    ('health-and-well-being', _('Health & Well-being')),
    ('education', _('Education')),
    ('gender-equality', _('Gender Equality')),
    ('sanitation', _('Sanitation')),
    ('climate-changes', _('Climate Change')),
    ('clean-energy', _('Clean Energy')),
    ('environmental-conservation', _('Environmental Conservation')),
    ('work-and-economic-growth', _('Work & Economic Growth')),
    ('human-rights', _('Human Rights')),
    ('social-justice', _('Social Justice')),
    ('art-and-culture', _('Arts & Culture'))
)

ORGANIZATIONAL_PROBLEM_CHOICES = (
    ('healthcare-supplies', _('Healthcare Supplies')),
    ('remote-working-tools', _('Remote Working Tools')),
    ('online-training', _('Online Training')),
    ('delivery-services', _('Delivery Services')),
    ('mentorship', _('Mentorship')),
    ('funding', _('Funding')),
    ('human-resources', _('Human Resources')),
)

USER_SERVICES = (
    ('healthcare-supplies', _('Healthcare Supplies')),
    ('people-power', _('People Power')),
    ('online-training', _('Online Training Tools')),
    ('delivery-services', _('Delivery Services')),
    ('mentorship', _('Mentorship')),
    ('funding', _('Funding')),
)

PUBLISHED_DATE_FORMAT = '%B %d, %Y'
