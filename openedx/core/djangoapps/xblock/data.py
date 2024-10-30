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


class AuthoredDataMode(Enum):
    """
    Runtime configuration which determines whether published or draft versions of content is used by default.
    """
    # Published only: used by the LMS. ONLY the published version of an XBlock is ever loaded. Users/APIs cannot request
    # the draft version nor a specific version.
    STRICTLY_PUBLISHED = 'published'
    # Default draft: used by Studio. By default the "lastest draft" version of an XBlock is used, but users/APIs can
    # also request to see the published version or any specific (old) version.
    DEFAULT_DRAFT = 'persisted'


class CheckPerm(Enum):
    """
    Options for the default permission check done by load_block()
    """
    # can view the published block and call handlers etc. but not necessarily view its OLX source nor field data
    CAN_LEARN = 1
    # read-only studio view: can see the block (draft or published), see its OLX, see its field data, etc.
    CAN_READ_AS_AUTHOR = 2
    # can view everything and make changes to the block
    CAN_EDIT = 3


class LatestVersion(Enum):
    """
    Options for specifying which version of an XBlock you want to load, if not specifying a specific version.
    """
    # Get the latest draft
    DRAFT = "draft"
    # Get the latest published version
    PUBLISHED = "published"
    # Get the default (based on AuthoredDataMode, i.e. published for LMS APIs, draft for Studio APIs)
    AUTO = "auto"
