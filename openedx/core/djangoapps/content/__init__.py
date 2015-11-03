"""
Setup the signals on startup.
"""
import openedx.core.djangoapps.content.course_structures.signals

# Importing this in this manner seems to resolve some inexplicable circular import issue.
# pylint: disable=relative-import
import course_structures
