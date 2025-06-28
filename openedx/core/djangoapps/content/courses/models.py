"""
These models form very low-level representations of Courses and Course Runs.

They don't hold much data on their own, but other apps can attach more useful
data to them.
"""
from __future__ import annotations

from logging import getLogger

from django.db import models
from django.utils.translation import gettext_lazy as _
from openedx_learning.api.authoring_models import LearningPackage

from openedx_learning.lib.fields import case_insensitive_char_field
from ..outline_roots.models import OutlineRoot

logger = getLogger()

__all__ = [
    "CatalogCourse",
    "Course",
]


class CatalogCourse(models.Model):
    """
    A catalog course is a collection of course runs.

    So for example, "Stanford Python 101" is a catalog course, and "Stanford
    Python 101 Spring 2025" is a course run of that course. Almost all
    interesting use cases are based around the course run - e.g. enrollment
    happens in a course run, content is authored in a course run, etc. But
    sometimes we need to deal with the related runs of the same course, so this
    model exists for those few times we need a reference to all of them.

    A CatalogCourse is not part of a particular learning package, because
    although we encourage each course's runs to be in the same learning package,
    that's neither a requirement nor always possible.
    """

    # Let's preserve case but avoid having org IDs that differ only in case.
    org_id = case_insensitive_char_field(
        null=False,
        blank=False,
        max_length=100,
        help_text=_(
            "The org ID. For a course with full course key 'course-v1:MITx+SC1x+1T2025', this would be 'MITx'"
        ),
    )

    # Let's preserve case but avoid having course IDs that differ only in case.
    course_id = case_insensitive_char_field(
        null=False,
        blank=False,
        max_length=100,
        help_text=_(
            "The course ID. For a course with full course key 'course-v1:MITx+SC1x+1T2025', this would be 'SC1x'"
        ),
    )

    class Meta:
        verbose_name = "Catalog Course"
        verbose_name_plural = "Catalog Courses"
        constraints = [
            models.UniqueConstraint(
                fields=["org_id", "course_id"],
                name="oel_courses_uniq_catalog_course_org_course_id",
            ),
        ]


class Course(models.Model):
    """
    A course [run] is a specific instance of a catalog course.

    In general, when we use the term "course" it refers to a Course Run.

    So for example, "Stanford Python 101" is a catalog course, and "Stanford
    Python 101 Spring 2025" is a Course Run.

    A Course Run is part of a learning package. Multiple course runs from the
    same catalog course can be part of the same learning package so that they
    can be more efficient (de-duplicating common data and assets). However, they
    are not required to be part of the same learning package, particularly when
    imported from legacy course representations.

    A Course Run is also a Learning Context.

    This model is called "Course" instead of "Course Run" for two reasons:
      (1) Because 99% of the time we use the term "course" in the code we are
          referring to a course run, so this is more consistent; and
      (2) Multiple versions of a catalog course may exist for reasons other than
          runs; for example, CCX may result in many Course variants of the same
          CatalogCourse - these aren't exactly "runs" but may still use separate
          instances of this model. TODO: validate this?

    This model is not versioned nor publishable. It also doesn't have much data,
    including even the name of the course. All useful data is available via
    versioned, related models like CourseMetadata (in edx-platform) or
    OutlineRoot. The name/title of the course is stored as the 'title' field of
    the OutlineRootVersion.PublishableEntityVersion.
    """
    catalog_course = models.ForeignKey(CatalogCourse, on_delete=models.CASCADE)
    learning_package = models.ForeignKey(LearningPackage, on_delete=models.CASCADE)
    source_course = models.ForeignKey(
        "Course",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        help_text=_(
            "If this course run is a re-run, this field indicates which previous run it was based on."
            # This field may have other meanings, e.g. for CCX courses in the future.
        ),
    )

    run = case_insensitive_char_field(  # Let's preserve case but avoid having run IDs that differ only in case.
        null=False,
        blank=False,
        max_length=100,
        help_text=_(
            "The course run. For a course with full course key 'course-v1:MITx+SC1x+1T2025', this would be '1T2025'."
        ),
    )

    # The outline root defines the content of this course run.
    # It's either a list of Sections, a list of Subsections, or a list of Units.
    outline_root = models.OneToOneField(
        OutlineRoot,
        on_delete=models.PROTECT,
        primary_key=True,
    )

    class Meta:
        verbose_name = "Course Run"
        verbose_name_plural = "Course Runs"
        constraints = [
            models.UniqueConstraint(
                # Regardless of which learning package the run is located in, each [catalog course + run] is unique.
                fields=["catalog_course", "run"],
                name="oel_courses_uniq_course_catalog_course_run",
            ),
        ]
