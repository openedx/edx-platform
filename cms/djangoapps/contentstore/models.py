"""
Models for contentstore
"""


from datetime import datetime, timezone

from config_models.models import ConfigurationModel
from django.db import models
from django.db.models import Count, F, Q, QuerySet
from django.db.models.fields import IntegerField, TextField
from django.db.models.functions import Coalesce
from django.db.models.lookups import GreaterThan
from django.utils.translation import gettext_lazy as _
from opaque_keys.edx.django.models import CourseKeyField, UsageKeyField
from opaque_keys.edx.keys import CourseKey, UsageKey
from openedx_learning.api.authoring_models import Component, PublishableEntity
from openedx_learning.lib.fields import (
    immutable_uuid_field,
    key_field,
    manual_date_time_field,
)


class VideoUploadConfig(ConfigurationModel):
    """
    Configuration for the video upload feature.

    .. no_pii:
    """
    profile_whitelist = TextField(
        blank=True,
        help_text="A comma-separated list of names of profiles to include in video encoding downloads."
    )

    @classmethod
    def get_profile_whitelist(cls):
        """Get the list of profiles to include in the encoding download"""
        return [profile for profile in cls.current().profile_whitelist.split(",") if profile]


class BackfillCourseTabsConfig(ConfigurationModel):
    """
    Manages configuration for a run of the backfill_course_tabs management command.

    .. no_pii:
    """

    class Meta:
        verbose_name = 'Arguments for backfill_course_tabs'
        verbose_name_plural = 'Arguments for backfill_course_tabs'

    start_index = IntegerField(
        help_text='Index of first course to start backfilling (in an alphabetically sorted list of courses)',
        default=0,
    )
    count = IntegerField(
        help_text='How many courses to backfill in this run (or zero for all courses)',
        default=0,
    )


class CleanStaleCertificateAvailabilityDatesConfig(ConfigurationModel):
    """
    Manages configuration for a run of the `clean_stale_certificate_availability_dates` management command.

    .. no_pii:
    """
    class Meta:
        app_label = "contentstore"
        verbose_name = "Arguments for 'clean_stale_certificate_availability_dates'"
        verbose_name_plural = "Arguments for 'clean_stale_certificate_availability_dates'"

    arguments = TextField(
        blank=True,
        help_text=(
            "A space seperated collection of arguments to be used when running the "
            "`clean_stale_certificate_available_dates` management command.' See the management command for options."
        )
    )


class PublishableEntityLink(models.Model):
    """
    This represents link between any two publishable entities or link between publishable entity and a course
    xblock. It helps in tracking relationship between xblocks imported from libraries and used in different courses.
    """
    uuid = immutable_uuid_field()
    upstream_block = models.ForeignKey(
        PublishableEntity,
        on_delete=models.SET_NULL,
        related_name="links",
        null=True,
        blank=True,
    )
    upstream_usage_key = UsageKeyField(
        max_length=255,
        help_text=_(
            "Upstream block usage key, this value cannot be null"
            " and useful to track upstream library blocks that do not exist yet"
        )
    )
    # Search by library/upstream context key
    upstream_context_key = key_field(
        help_text=_("Upstream context key i.e., learning_package/library key"),
        db_index=True,
    )
    # A downstream entity can only link to single upstream entity
    # whereas an entity can be upstream for multiple downstream entities.
    downstream_usage_key = UsageKeyField(max_length=255, unique=True)
    # Search by course/downstream key
    downstream_context_key = CourseKeyField(max_length=255, db_index=True)
    version_synced = models.IntegerField()
    version_declined = models.IntegerField(null=True, blank=True)
    created = manual_date_time_field()
    updated = manual_date_time_field()

    def __str__(self):
        return f"{self.upstream_usage_key}->{self.downstream_usage_key}"

    @property
    def upstream_version(self) -> int | None:
        """
        Returns upstream block version number if available.
        """
        version_num = None
        if hasattr(self.upstream_block, 'published'):
            if hasattr(self.upstream_block.published, 'version'):
                if hasattr(self.upstream_block.published.version, 'version_num'):
                    version_num = self.upstream_block.published.version.version_num
        return version_num

    @property
    def upstream_context_title(self) -> str:
        """
        Returns upstream context title.
        """
        return self.upstream_block.learning_package.title

    class Meta:
        verbose_name = _("Publishable Entity Link")
        verbose_name_plural = _("Publishable Entity Links")

    @classmethod
    def update_or_create(
        cls,
        upstream_block: Component | None,
        /,
        upstream_usage_key: UsageKey,
        upstream_context_key: str,
        downstream_usage_key: UsageKey,
        downstream_context_key: CourseKey,
        version_synced: int,
        version_declined: int | None = None,
        created: datetime | None = None,
    ) -> "PublishableEntityLink":
        """
        Update or create entity link. This will only update `updated` field if something has changed.
        """
        if not created:
            created = datetime.now(tz=timezone.utc)
        new_values = {
            'upstream_usage_key': upstream_usage_key,
            'upstream_context_key': upstream_context_key,
            'downstream_usage_key': downstream_usage_key,
            'downstream_context_key': downstream_context_key,
            'version_synced': version_synced,
            'version_declined': version_declined,
        }
        if upstream_block:
            new_values.update(
                {
                    'upstream_block': upstream_block.publishable_entity,
                }
            )
        try:
            link = cls.objects.get(downstream_usage_key=downstream_usage_key)
            # TODO: until we save modified datetime for course xblocks in index, the modified time for links are updated
            # everytime a downstream/course block is updated. This allows us to order links[1] based on recently
            # modified downstream version.
            # pylint: disable=line-too-long
            # 1. https://github.com/open-craft/frontend-app-course-authoring/blob/0443d88824095f6f65a3a64b77244af590d4edff/src/course-libraries/ReviewTabContent.tsx#L222-L233
            has_changes = True  # change to false once above condition is met.
            for key, value in new_values.items():
                prev = getattr(link, key)
                # None != None is True, so we need to check for it specially
                if prev != value and ~(prev is None and value is None):
                    has_changes = True
                    setattr(link, key, value)
            if has_changes:
                link.updated = created
                link.save()
        except cls.DoesNotExist:
            link = cls(**new_values)
            link.created = created
            link.updated = created
            link.save()
        return link

    @classmethod
    def filter_links(
        cls,
        **link_filter,
    ) -> QuerySet["PublishableEntityLink"]:
        """
        Get all links along with sync flag, upstream context title and version, with optional filtering.
        """
        ready_to_sync = link_filter.pop('ready_to_sync', None)
        result = cls.objects.filter(**link_filter).select_related(
            "upstream_block__published__version",
            "upstream_block__learning_package"
        ).annotate(
            ready_to_sync=(
                GreaterThan(
                    Coalesce("upstream_block__published__version__version_num", 0),
                    Coalesce("version_synced", 0)
                ) & GreaterThan(
                    Coalesce("upstream_block__published__version__version_num", 0),
                    Coalesce("version_declined", 0)
                )
            )
        )
        if ready_to_sync is not None:
            result = result.filter(ready_to_sync=ready_to_sync)
        return result

    @classmethod
    def get_by_upstream_usage_key(cls, upstream_usage_key: UsageKey) -> QuerySet["PublishableEntityLink"]:
        """
        Get all downstream context keys for given upstream usage key
        """
        return cls.objects.filter(
            upstream_usage_key=upstream_usage_key,
        )

    @classmethod
    def summarize_by_downstream_context(cls, downstream_context_key: CourseKey) -> QuerySet:
        """
        Returns a summary of links by upstream context for given downstream_context_key.
        Example:
        [
            {
                "upstream_context_title": "CS problems 3",
                "upstream_context_key": "lib:OpenedX:CSPROB3",
                "ready_to_sync_count": 11,
                "total_count": 14
            },
            {
                "upstream_context_title": "CS problems 2",
                "upstream_context_key": "lib:OpenedX:CSPROB2",
                "ready_to_sync_count": 15,
                "total_count": 24
            },
        ]
        """
        result = cls.filter_links(downstream_context_key=downstream_context_key).values(
            "upstream_context_key",
            upstream_context_title=F("upstream_block__learning_package__title"),
        ).annotate(
            ready_to_sync_count=Count("id", Q(ready_to_sync=True)),
            total_count=Count('id')
        )
        return result


class LearningContextLinksStatusChoices(models.TextChoices):
    """
    Enumerates the states that a LearningContextLinksStatus can be in.
    """
    PENDING = "pending", _("Pending")
    PROCESSING = "processing", _("Processing")
    FAILED = "failed", _("Failed")
    COMPLETED = "completed", _("Completed")


class LearningContextLinksStatus(models.Model):
    """
    This table stores current processing status of upstream-downstream links in PublishableEntityLink table for a
    course or a learning context.
    """
    context_key = CourseKeyField(
        max_length=255,
        # Single entry for a learning context or course
        unique=True,
        help_text=_("Linking status for course context key"),
    )
    status = models.CharField(
        max_length=20,
        choices=LearningContextLinksStatusChoices.choices,
        help_text=_("Status of links in given learning context/course."),
    )
    created = manual_date_time_field()
    updated = manual_date_time_field()

    class Meta:
        verbose_name = _("Learning Context Links status")
        verbose_name_plural = _("Learning Context Links status")

    def __str__(self):
        return f"{self.status}|{self.context_key}"

    @classmethod
    def get_or_create(cls, context_key: str, created: datetime | None = None) -> "LearningContextLinksStatus":
        """
        Get or create course link status row from LearningContextLinksStatus table for given course key.

        Args:
            context_key: Learning context or Course key

        Returns:
            LearningContextLinksStatus object
        """
        if not created:
            created = datetime.now(tz=timezone.utc)
        status, _ = cls.objects.get_or_create(
            context_key=context_key,
            defaults={
                'status': LearningContextLinksStatusChoices.PENDING,
                'created': created,
                'updated': created,
            },
        )
        return status

    def update_status(
        self,
        status: LearningContextLinksStatusChoices,
        updated: datetime | None = None
    ) -> None:
        """
        Updates entity links processing status of given learning context.
        """
        self.status = status
        self.updated = updated or datetime.now(tz=timezone.utc)
        self.save()
