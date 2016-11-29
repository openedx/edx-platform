"""
Constants and Query definition associated with data_access
"""
import re
from django.conf import settings


class StudentQuery(object):
    """
    Encapsulates a query in the instructor dashboard email lists tool
    """
    def __init__(self, query_type, inclusion, entity_id, filtering, entity_name):
        self.query_type = query_type
        self.inclusion = inclusion
        self.entity_id = entity_id
        self.filter = filtering
        self.entity_name = entity_name


class QueryOrigin:
    """
    Where a query issued originated
    """
    EMAIL = "EMAIL"
    WIDGET = "WIDGET"

QUERYORIGIN_MAP = {QueryOrigin.EMAIL: 'E',
                   QueryOrigin.WIDGET: 'W'}


class Inclusion:
    """
    Options for combining queries
    """
    AND = "AND"
    OR = "OR"
    NOT = "NOT"
    FILTER = "FILTER"


INCLUSION_MAP = {Inclusion.AND: 'A',
                 Inclusion.OR: 'O',
                 Inclusion.NOT: 'N',
                 Inclusion.FILTER: 'F'}


REVERSE_INCLUSION_MAP = {'A': Inclusion.AND,
                         'O': Inclusion.OR,
                         'N': Inclusion.NOT,
                         'F': Inclusion.FILTER}

INCLUDE_SECTION_PATTERN = re.compile('chapter|sequential')
INCLUDE_PROBLEM_PATTERN = re.compile('|'.join(settings.INSTRUCTOR_QUERY_PROBLEM_TYPES))
TEMPORARY_QUERY_LIFETIME = 15  # in minutes, how long a temporary query lives before it gets purged


class SectionFilters:
    """
    Possible filters we may have for sections
    """
    OPENED = "opened"
    NOT_OPENED = "not opened"
    COMPLETED = "completed"


class ProblemFilters:
    """
    Possible filters we may have for problems
    """
    OPENED = SectionFilters.OPENED
    NOT_OPENED = SectionFilters.NOT_OPENED
    COMPLETED = "completed"
    NOT_COMPLETED = "not completed"
    SCORE = "score"
    NUMBER_PEER_GRADED = "number peer graded"

ALL_SECTION_FILTERS = {filter for filter in [SectionFilters.OPENED,
                                             SectionFilters.NOT_OPENED,
                                             SectionFilters.COMPLETED,
                                             ]}

ALL_PROBLEM_FILTERS = {filter for filter in [ProblemFilters.OPENED,
                                             ProblemFilters.NOT_OPENED,
                                             ProblemFilters.COMPLETED,
                                             ProblemFilters.NOT_COMPLETED,
                                             ProblemFilters.SCORE,
                                             ProblemFilters.NUMBER_PEER_GRADED,
                                             ]}


class QueryType:
    """
    Types for queries
    """
    SECTION = "Section"
    PROBLEM = "Problem"


class DatabaseFields:
    """
    Database columns
    """
    STUDENT_ID = "student_id"
    STUDENT_EMAIL = "student__email"
    ID = "id"
    EMAIL = "email"
    QUERY_ID = "query_id"
    QUERY = "query"
    USER_ID = "user_id"
    PROFILE_NAME = "profile__name"


class QueryStatus:
    """
    Stores possible statuses for queries
    """
    WORKING = "working"
    COMPLETED = "completed"
