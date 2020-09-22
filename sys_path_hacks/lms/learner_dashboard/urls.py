import warnings
warnings.warn("Importing learner_dashboard.urls instead of lms.djangoapps.learner_dashboard.urls is deprecated", stacklevel=2)

from lms.djangoapps.learner_dashboard.urls import *
