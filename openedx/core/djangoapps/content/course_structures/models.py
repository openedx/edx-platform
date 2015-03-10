import json
import logging

from model_utils.models import TimeStampedModel

from util.models import CompressedTextField
from xmodule_django.models import CourseKeyField


logger = logging.getLogger(__name__)  # pylint: disable=invalid-name


class CourseStructure(TimeStampedModel):
    course_id = CourseKeyField(max_length=255, db_index=True, unique=True, verbose_name='Course ID')

    # Right now the only thing we do with the structure doc is store it and
    # send it on request. If we need to store a more complex data model later,
    # we can do so and build a migration. The only problem with a normalized
    # data model for this is that it will likely involve hundreds of rows, and
    # we'd have to be careful about caching.
    structure_json = CompressedTextField(verbose_name='Structure JSON', blank=True, null=True)

    @property
    def structure(self):
        if self.structure_json:
            return json.loads(self.structure_json)
        return None

# Signals must be imported in a file that is automatically loaded at app startup (e.g. models.py). We import them
# at the end of this file to avoid circular dependencies.
import signals  # pylint: disable=unused-import
