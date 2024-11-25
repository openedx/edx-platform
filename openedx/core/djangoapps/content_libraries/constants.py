""" Constants used for the content libraries. """
from django.utils.translation import gettext_lazy as _

<<<<<<< HEAD
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
=======
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374

# These are all the licenses we support so far.
ALL_RIGHTS_RESERVED = ''
CC_4_BY = 'CC:4.0:BY'
CC_4_BY_NC = 'CC:4.0:BY:NC'
CC_4_BY_NC_ND = 'CC:4.0:BY:NC:ND'
CC_4_BY_NC_SA = 'CC:4.0:BY:NC:SA'
CC_4_BY_ND = 'CC:4.0:BY:ND'
CC_4_BY_SA = 'CC:4.0:BY:SA'

LICENSE_OPTIONS = (
    (ALL_RIGHTS_RESERVED, _('All Rights Reserved.')),
    (CC_4_BY, _('Creative Commons Attribution 4.0')),
    (CC_4_BY_NC, _('Creative Commons Attribution-NonCommercial 4.0')),
    (CC_4_BY_NC_ND, _('Creative Commons Attribution-NonCommercial-NoDerivatives 4.0')),
    (CC_4_BY_NC_SA, _('Creative Commons Attribution-NonCommercial-ShareAlike 4.0')),
    (CC_4_BY_ND, _('Creative Commons Attribution-NoDerivatives 4.0')),
    (CC_4_BY_SA, _('Creative Commons Attribution-ShareAlike 4.0'))
)
