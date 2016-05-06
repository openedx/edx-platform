"""
This module has implementation of celery tasks to compute course aggregate metadata
"""

import logging

from celery.task import task
from opaque_keys.edx.keys import CourseKey

from openedx.core.djangoapps.content.course_metadata.models import CourseAggregatedMetaData
from openedx.core.djangoapps.content.course_metadata.utils import get_course_leaf_nodes

log = logging.getLogger('edx.celery.task')


@task(name=u'openedx.core.djangoapps.content.course_metadata.tasks.update_course_aggregate_metadata')
def update_course_aggregate_metadata(course_key):  # pylint: disable=invalid-name
    """
    Regenerates and updates the course aggregate metadata (in the database) for the specified course.
    """
    if not isinstance(course_key, basestring):
        raise ValueError('course_key must be a string. {} is not acceptable.'.format(type(course_key)))

    course_key = CourseKey.from_string(course_key)

    try:
        course_leaf_nodes = get_course_leaf_nodes(course_key)
    except Exception as ex:
        log.exception('An error occurred while retrieving course assessments: %s', ex.message)
        raise

    course_metadata, __ = CourseAggregatedMetaData.objects.get_or_create(id=course_key)
    course_metadata.total_assessments = len(course_leaf_nodes)
    course_metadata.save()
