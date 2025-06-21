"""Models for XBlock runtime."""
from django.db import models
from jsonfield.fields import JSONField
from openedx_learning.api.authoring_models import PublishableEntity, PublishableEntityVersionMixin
from opaque_keys.edx.django.models import CourseKeyField, LearningContextKeyField, UsageKeyField

import bson

class XBlockVersionFieldData(PublishableEntityVersionMixin):
    """
    Optimized storage of parsed XBlock field data.

    This model stores the parsed field data from XBlock OLX content to avoid repeated XML parsing on every block load.
    It maintains a 1:1 relationship with PublishableEntityVersion and caches both content and settings scope fields.
    When block field data changes, a new ComponentVersion and corresponding XBlockVersionFieldData record
    are created by the LearningCoreXBlockRuntime.
    """
    def generate_object_id_str():
        # TODO: This should be a proper field type
        return str(bson.ObjectId())

    # This exists entirely for the Modulestore shim layer. We can get rid of it
    # when we've moved entirely off of SplitModuleStore.
    definition_object_id = models.CharField(
        max_length=24,
        null=False,
        unique=True,
        default=generate_object_id_str,
    )

    content = JSONField(
        default=dict,
        help_text="XBlock content scope fields as JSON"
    )

    settings = JSONField(
        default=dict,
        help_text="XBlock settings scope fields as JSON"
    )

    children = JSONField(
        default=None,
        help_text="XBlock children scope fields as JSON"
    )

    class Meta:
        verbose_name = "XBlock Version Field Data"
        verbose_name_plural = "XBlock Version Field Data"

    def __str__(self):
        return f"Field data for {self.publishable_entity_version}"


class LearningCoreCourseStructure(models.Model):
    course_key = CourseKeyField(max_length=255)
    structure = models.BinaryField()

    class Meta:
        constraints = [
            models.UniqueConstraint("course_key", name="xblock_lccs_uniq_course_key")
        ]


class LearningCoreLearningContext(models.Model):
    key = LearningContextKeyField(max_length=255, unique=True)
    root = models.ForeignKey('Block', on_delete=models.SET_NULL, null=True)

    # This is a way for us to turn off LC as a backend both for rollback
    # purposes, but also to temporarily disable when doing a re-import.
    use_learning_core = models.BooleanField(default=True)


class Block(models.Model):
    learning_context = models.ForeignKey(LearningCoreLearningContext, on_delete=models.CASCADE)
    key = UsageKeyField(max_length=255, unique=True)
    entity = models.OneToOneField(PublishableEntity, on_delete=models.RESTRICT)
