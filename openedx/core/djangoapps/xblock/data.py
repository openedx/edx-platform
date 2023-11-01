"""
Data structures for the XBlock Django app's python APIs
"""
from enum import Enum


class StudentDataMode(Enum):
    """
    Is student data (like which answer was selected) persisted in the DB or just stored temporarily in the session?
    Generally, the LMS uses persistence and Studio uses ephemeral data.
    """
    Ephemeral = 'ephemeral'
    Persisted = 'persisted'
