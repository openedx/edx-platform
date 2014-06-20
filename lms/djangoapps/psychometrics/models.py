#
# db model for psychometrics data
#
# this data is collected in real time
#

from django.db import models
from courseware.models import StudentModule


class PsychometricData(models.Model):
    """
    This data is a table linking student, module, and module performance,
    including number of attempts, grade, max grade, and time of checks.

    Links to instances of StudentModule, but only those for capa problems.

    Note that StudentModule.module_state_key is a :class:`Location` instance.

    checktimes is extracted from tracking logs, or added by capa module via psychometrics callback.
    """

    studentmodule = models.ForeignKey(StudentModule, db_index=True, unique=True)   # contains student, module_state_key, course_id

    done = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)			# extracted from studentmodule.state
    checktimes = models.TextField(null=True, blank=True)  	# internally stored as list of datetime objects

    # keep in mind
    # grade = studentmodule.grade
    # max_grade = studentmodule.max_grade
    # student = studentmodule.student
    # course_id = studentmodule.course_id
    # location = studentmodule.module_state_key

    def __unicode__(self):
        sm = self.studentmodule
        return "[PsychometricData] %s url=%s, grade=%s, max=%s, attempts=%s, ct=%s" % (sm.student,
                                                                                       sm.module_state_key,
                                                                                       sm.grade,
                                                                                       sm.max_grade,
                                                                                       self.attempts,
                                                                                       self.checktimes)
