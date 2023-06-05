"""
Models for Learning Sequences and Course Outline generation.

Conventions:

1. Only things in the `api` package should ever import this file. Do NOT import
from views.py or anywhere else. Even if that means we have to give up some DRF
niceties.

2. The vast majority of what our public API promises should be efficiently
queryable with these models. We might occasionally reach into other systems
built for fast course-level queries (e.g. grading, scheduling), but we should
never touch ModuleStore or Block Transformers.

3. It's okay for some basic validation to happen at the model layer. Constraints
like uniqueness should absolutely be enforced at this layer. But business logic
should happen in the `api` package.

4. Try to avoid blob-like entites (e.g. JSON fields) as much as possible and
push things into normalized tables.

5. In general, keep models as a thin, dumb persistence layer. Let the `api`
package decide when and where it's safe to cache things.

6. Models and data.py datastructures don't have to map 1:1, but the convention
is that the data struct has a "...Data" appended to it. For instance,
LearningContext -> LearningContextData. This is because the Python name for
dataclasses (what attrs is close to), and for better backwards compatibility if
we want to adopt this convention elsewhere.

7. Strongly separate things that are intrinsic to Learning Sequences as a whole
vs. things that only apply to Sequences in the context of a Course. We have
other uses for sequences (e.g. Content Libraries, Pathways) and we want to keep
that separated.

8. Your app _may_ make foreign keys to models in this app, but you should limit
yourself to the LearningContext and LearningSequence models. Other tables are
not guaranteed to stick around, and values may be deleted unexpectedly.
"""
from django.db import models
from model_utils.models import TimeStampedModel

from opaque_keys.edx.django.models import (
    CourseKeyField, LearningContextKeyField, UsageKeyField
)
from .data import CourseVisibility


class LearningContext(TimeStampedModel):
    """
    These are used to group Learning Sequences so that many of them can be
    pulled at once. We use this instead of a foreign key to CourseOverview
    because this table can contain things that are not courses.

    It is okay to make a foreign key against this table.
    """
    id = models.BigAutoField(primary_key=True)
    context_key = LearningContextKeyField(
        max_length=255, db_index=True, unique=True, null=False
    )
    title = models.CharField(max_length=255)
    published_at = models.DateTimeField(null=False)
    published_version = models.CharField(max_length=255)

    class Meta:
        indexes = [
            models.Index(fields=['-published_at'])
        ]


class CourseContext(TimeStampedModel):
    """
    A model containing course specific information e.g course_visibility
    """
    learning_context = models.OneToOneField(
        LearningContext, on_delete=models.CASCADE, primary_key=True, related_name="course_context"
    )
    # Please note, the tuple is intentionally use value for both actual value and display value
    # because the name of enum constant is written in upper while the values are lower
    course_visibility = models.CharField(
        max_length=32, choices=[(constant.value, constant.value) for constant in CourseVisibility]
    )
    days_early_for_beta = models.IntegerField(null=True, blank=True)
    self_paced = models.BooleanField(default=False)


class LearningSequence(TimeStampedModel):
    """
    The reason why this model doesn't have a direct foreign key to CourseSection
    is because we eventually want to have LearningSequences that exist outside
    of courses. Attributes that apply directly to all LearningSequences
    (usage_key, title, learning_context, etc.) will apply here, but anything
    that is specific to how a LearningContext is rendered for a course (e.g.
    permissions, staff visibility, is_entrance_exam) wil live in
    CourseSectionSequence.

    It is okay to make a foreign key against this table.
    """
    id = models.BigAutoField(primary_key=True)
    learning_context = models.ForeignKey(
        LearningContext, on_delete=models.CASCADE, related_name='sequences'
    )
    usage_key = UsageKeyField(max_length=255)

    # Yes, it's crazy to have a title 1K chars long. But we have ones at least
    # 270 long, meaning we wouldn't be able to make it indexed anyway in InnoDB.
    title = models.CharField(max_length=1000)

    # Separate field for when this Sequence's content was last changed?
    class Meta:
        unique_together = [
            ['learning_context', 'usage_key'],
        ]


class CourseContentVisibilityMixin(models.Model):
    """
    This mixin stores XBlock information that affects outline level visibility
    for a single LearningSequence or Section in a course.

    We keep the XBlock field names here, even if they're somewhat misleading.
    Please read the comments carefully for each field.
    """
    # This is an obscure, OLX-only flag (there is no UI for it in Studio) that
    # lets you define a Sequence that is reachable by direct URL but not shown
    # in Course navigation. It was used for things like supplementary tutorials
    # that were not considered a part of the normal course path.
    hide_from_toc = models.BooleanField(null=False, default=False)

    # Restrict visibility to course staff, regardless of start date. This is
    # often used to hide content that either still being built out, or is a
    # scratch space of content that will eventually be copied over to other
    # sequences.
    visible_to_staff_only = models.BooleanField(null=False, default=False)

    class Meta:
        abstract = True


class CourseSection(CourseContentVisibilityMixin, TimeStampedModel):
    """
    Course Section data, mapping to the 'chapter' block type.

    Do NOT make a foreign key against this table, as the values are deleted and
    re-created on course publish.
    """
    id = models.BigAutoField(primary_key=True)
    course_context = models.ForeignKey(
        CourseContext, on_delete=models.CASCADE, related_name='sections'
    )
    usage_key = UsageKeyField(max_length=255)
    title = models.CharField(max_length=1000)

    # What is our position within the Course? (starts with 0)
    ordering = models.PositiveIntegerField(null=False)

    class Meta:
        unique_together = [
            ['course_context', 'usage_key'],
        ]
        index_together = [
            ['course_context', 'ordering'],
        ]


class CourseSectionSequence(CourseContentVisibilityMixin, TimeStampedModel):
    """
    This is a join+ordering table, with entries that could get wiped out and
    recreated with every course publish. Do NOT make a ForeignKey against this
    table before implementing smarter replacement logic when publishing happens,
    or you'll see deletes all the time.

    CourseContentVisibilityMixin is applied here (and not in LearningSequence)
    because CourseContentVisibilityMixin describes attributes that are part of
    how a LearningSequence is used within a course, and may not apply to other
    kinds of LearningSequences.

    Do NOT make a foreign key against this table, as the values are deleted and
    re-created on course publish.
    """
    id = models.BigAutoField(primary_key=True)
    course_context = models.ForeignKey(
        CourseContext, on_delete=models.CASCADE, related_name='section_sequences'
    )
    section = models.ForeignKey(CourseSection, on_delete=models.CASCADE)
    sequence = models.ForeignKey(LearningSequence, on_delete=models.CASCADE)

    # Make the sequence inaccessible from the outline after the due date has passed
    inaccessible_after_due = models.BooleanField(null=False, default=False)

    # Ordering, starts with 0, but global for the course. So if you had 200
    # sequences across 20 sections, the numbering here would be 0-199.
    ordering = models.PositiveIntegerField(null=False)

    class Meta:
        unique_together = [
            ['course_context', 'ordering'],
        ]
