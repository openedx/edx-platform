"""Constants for courseware"""

PRE_ASSESSMENT_FORMAT = 'pre assessment'
POST_ASSESSMENT_FORMAT = 'post assessment'
COMPETENCY_ASSESSMENT_DEFAULT_PROBLEMS_COUNT = 5

COMP_ASSESS_RECORD_SUCCESS_MSG = 'Attempt successfully recorded.'
INVALID_PROBLEM_ID_MSG = 'Problem Id is not valid.'

COMPETENCY_ASSESSMENT_TYPE_CHOICES = (
    ('pre', 'Pre Assessment'),
    ('post', 'Post Assesment')
)
CORRECTNESS_CHOICES = (
    ('correct', 'Correct'),
    ('incorrect', 'Incorrect'),
    ('submitted', 'Submitted'),
)
