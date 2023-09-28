"""
Models for configuration of the feature flags
controlling persistent grades.
"""


from config_models.models import ConfigurationModel
from django.db.models import IntegerField, TextField


class ComputeGradesSetting(ConfigurationModel):
    """
    .. no_pii:
    """
    class Meta:
        app_label = "grades"

    batch_size = IntegerField(default=100)
    course_ids = TextField(
        blank=False,
        help_text="Whitespace-separated list of course keys for which to compute grades."
    )
