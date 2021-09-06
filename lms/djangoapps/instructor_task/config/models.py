"""
Models for configuration of settings relevant
to instructor tasks.
"""


from config_models.models import ConfigurationModel
from django.db.models import IntegerField


class GradeReportSetting(ConfigurationModel):
    """
    Sets the batch size used when running grade reports
    with multiple celery workers.

    .. no_pii:
    """
    batch_size = IntegerField(default=100)
