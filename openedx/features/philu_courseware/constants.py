"""Constants for courseware"""

PRE_ASSESSMENT_FORMAT = 'pre assessment'
POST_ASSESSMENT_FORMAT = 'post assessment'
COMPETENCY_ASSESSMENT_DEFAULT_PROBLEMS_COUNT = 5

INVALID_PROBLEM_ID_MSG = 'Problem Id is not valid.'

PRE_ASSESSMENT_KEY = 'pre'
POST_ASSESSMENT_KEY = 'post'
CORRECT_ASSESSMENT_KEY = 'correct'

COMPETENCY_ASSESSMENT_TYPE_CHOICES = (
    (PRE_ASSESSMENT_KEY, 'Pre Assessment'),
    (POST_ASSESSMENT_KEY, 'Post Assesment')
)
CORRECTNESS_CHOICES = (
    ('correct', 'Correct'),
    ('incorrect', 'Incorrect'),
    ('submitted', 'Submitted'),
)
