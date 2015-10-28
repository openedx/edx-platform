"""
The Course Blocks app, built upon the Block Cache framework in
openedx.core.lib.block_cache, is a higher layer django app in LMS that
provides additional context of Courses and Users (via usage_info.py) with
implementations for Block Structure Transformers that are related to
block structure course access.

As described in the Block Cache framework's __init__ module, this
framework provides faster access to course blocks for performance
sensitive features, by caching all transformer-required data so no
modulestore access is necessary during block access.

It is expected that only Block Access related transformers reside in
this django app, as they are cross-cutting authorization transformers
required across other features. Other higher-level and feature-specific
transformers should be implemented in their own separate apps.

Note: Currently, some of the implementation is redundant with the
has_access code in courseware/access.py. However, we do have short-term
plans for refactoring the current has_access code to use Course Blocks
instead (https://openedx.atlassian.net/browse/MA-1019).  We have
introduced this redundancy in the short-term as an incremental
implementation approach, reducing risk with initial release of this app.
"""

# Importing signals is necessary to activate the course publish/delete signal handlers.
from . import signals  # pylint: disable=unused-import
