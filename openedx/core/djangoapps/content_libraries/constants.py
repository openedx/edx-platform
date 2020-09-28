""" Constants used for the content libraries. """
from django.utils.translation import ugettext_lazy as _

# ./api.py and ./views.py are only used in Studio, so we always work with this draft of any
# content library bundle:
DRAFT_NAME = 'studio_draft'

VIDEO = 'video'
COMPLEX = 'complex'
PROBLEM = 'problem'

LIBRARY_TYPES = (
    (VIDEO, _('Video')),
    (COMPLEX, _('Complex')),
    (PROBLEM, _('Problem')),
)
