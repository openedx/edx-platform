"""Models for XBlock runtime."""
from jsonfield.fields import JSONField
from openedx_learning.api.authoring_models import PublishableEntityVersionMixin


class XBlockVersionFieldData(PublishableEntityVersionMixin):
    """
    Optimized storage of parsed XBlock field data.

    This model stores the parsed field data from XBlock OLX content to avoid repeated XML parsing on every block load.
    It maintains a 1:1 relationship with PublishableEntityVersion and caches both content and settings scope fields.
    When block field data changes, a new ComponentVersion and corresponding XBlockVersionFieldData record
    are created by the LearningCoreXBlockRuntime.
    """

    content = JSONField(
        default=dict,
        help_text="XBlock content scope fields as JSON"
    )

    settings = JSONField(
        default=dict,
        help_text="XBlock settings scope fields as JSON"
    )

    class Meta:
        verbose_name = "XBlock Version Field Data"
        verbose_name_plural = "XBlock Version Field Data"

    def __str__(self):
        return f"Field data for {self.publishable_entity_version}"
