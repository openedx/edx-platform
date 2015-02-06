import json

from django.db import models
from django.dispatch import receiver
from celery.task import task
from model_utils.models import TimeStampedModel

from opaque_keys.edx.keys import CourseKey

from xmodule.modulestore.django import modulestore, SignalHandler
from xmodule_django.models import CourseKeyField

class CourseStructure(TimeStampedModel):

    course_id = CourseKeyField(max_length=255, db_index=True)
    version = models.CharField(max_length=255, blank=True, default="")

    # Right now the only thing we do with the structure doc is store it and
    # send it on request. If we need to store a more complex data model later,
    # we can do so and build a migration. The only problem with a normalized
    # data model for this is that it will likely involve hundreds of rows, and
    # we'd have to be careful about caching.
    structure_json = models.TextField()

    # Index together:
    #   (course_id, version)
    #   (course_id, created)


def course_structure(course_key):
    course = modulestore().get_course(course_key, depth=None)
    blocks_stack = [course]
    blocks_dict = {}
    while blocks_stack:
        curr_block = blocks_stack.pop()
        children = curr_block.get_children() if curr_block.has_children else []       
        blocks_dict[unicode(curr_block.scope_ids.usage_id)] = {
            "usage_key": unicode(curr_block.scope_ids.usage_id),
            "block_type": curr_block.category,
            "display_name": curr_block.display_name,
            "graded": curr_block.graded,
            "format": curr_block.format,
            "children": [unicode(ch.scope_ids.usage_id) for ch in children]
        }
        blocks_stack.extend(children)
    return {
        "root": unicode(course.scope_ids.usage_id),
        "blocks": blocks_dict
    }

@receiver(SignalHandler.course_published)
def listen_for_course_publish(sender, course_key, **kwargs):
    update_course_structure(course_key)

@task()
def update_course_structure(course_key):
    structure = course_structure(course_key)
    CourseStructure.objects.create(
        course_id=unicode(course_key),
        structure_json=json.dumps(structure),
        version="",
    )
