from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class LearningSequencesConfig(AppConfig):
    name = 'openedx.core.djangoapps.content.learning_sequences'
    verbose_name = _('Learning Sequences')

    def ready(self):
        # Register celery workers
        # from .tasks import ls_listen_for_course_publish  # pylint: disable=unused-variable
        pass
