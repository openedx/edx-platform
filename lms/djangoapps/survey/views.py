"""
View endpoints for Survey
"""

import logging
from student.models import User

from survey.models import SurveyForm, SurveyAnswer

log = logging.getLogger("edx.survey")
