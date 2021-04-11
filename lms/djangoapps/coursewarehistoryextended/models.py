"""
WE'RE USING MIGRATIONS!

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py schemamigration courseware --auto description_of_your_change
3. Add the migration file created in edx-platform/lms/djangoapps/coursewarehistoryextended/migrations/


ASSUMPTIONS: modules have unique IDs, even across different module_types

"""


import six
from django.db import models
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from django.utils.encoding import python_2_unicode_compatible

from lms.djangoapps.courseware.models import BaseStudentModuleHistory, StudentModule
from lms.djangoapps.courseware.fields import UnsignedBigIntAutoField


@python_2_unicode_compatible
class StudentModuleHistoryExtended(BaseStudentModuleHistory):
    """Keeps a complete history of state changes for a given XModule for a given
    Student. Right now, we restrict this to problems so that the table doesn't
    explode in size.

    This new extended CSMH has a larger primary key that won't run out of space
    so quickly."""

    class Meta(object):
        app_label = 'coursewarehistoryextended'
        get_latest_by = "created"
        index_together = ['student_module']

    id = UnsignedBigIntAutoField(primary_key=True)  # pylint: disable=invalid-name

    student_module = models.ForeignKey(StudentModule, db_index=True, db_constraint=False, on_delete=models.DO_NOTHING)

    @receiver(post_save, sender=StudentModule)
    def save_history(sender, instance, **kwargs):  # pylint: disable=no-self-argument, unused-argument
        """
        Checks the instance's module_type, and creates & saves a
        StudentModuleHistoryExtended entry if the module_type is one that
        we save.
        """
        if instance.module_type in StudentModuleHistoryExtended.HISTORY_SAVING_TYPES:
            history_entry = StudentModuleHistoryExtended(student_module=instance,
                                                         version=None,
                                                         created=instance.modified,
                                                         state=instance.state,
                                                         grade=instance.grade,
                                                         max_grade=instance.max_grade)
            history_entry.save()

    @receiver(post_delete, sender=StudentModule)
    def delete_history(sender, instance, **kwargs):  # pylint: disable=no-self-argument, unused-argument
        """
        Django can't cascade delete across databases, so we tell it at the model level to
        on_delete=DO_NOTHING and then listen for post_delete so we can clean up the CSMHE rows.
        """
        StudentModuleHistoryExtended.objects.filter(student_module=instance).all().delete()

    def __str__(self):
        return six.text_type(repr(self))
