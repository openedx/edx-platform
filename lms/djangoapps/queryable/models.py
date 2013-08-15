from django.contrib.auth.models import User
from django.db import models
from courseware.models import StudentModule

class StudentModuleExpand(models.Model):
    """
    Expanded version of courseware's model StudentModule. This is only for
    instances of module type 'problem'. Adds attribute 'attempts' that is pulled
    out of the json in the state attribute.
    """
    
    EXPAND_TYPES = {'problem'}

    student_module = models.ForeignKey(StudentModule, db_index=True)

    # The value mapped to 'attempts' in the json in state
    attempts = models.IntegerField(null=True, blank=True, db_index=True)

    # Values from StudentModule
    module_type = models.CharField(max_length=32, default='problem', db_index=True)
    module_state_key = models.CharField(max_length=255, db_index=True, db_column='module_id')
    student = models.ForeignKey(User, db_index=True)
    course_id = models.CharField(max_length=255, db_index=True)

    class Meta:
        unique_together = (('student', 'module_state_key', 'course_id'),)

    grade = models.FloatField(null=True, blank=True, db_index=True)
    max_grade = models.FloatField(null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    modified = models.DateTimeField(auto_now=True, db_index=True)


class CourseGrade(models.Model):
    """
    Holds student's overall course grade as a percentage and letter grade (if letter grade present).
    """

    user = models.ForeignKey(User, db_index=True)
    course_id = models.CharField(max_length=255, db_index=True)

    percent = models.FloatField(db_index=True, null=True)
    grade = models.CharField(max_length=32, db_index=True, null=True)

    class Meta:
        unique_together = (('user', 'course_id'), )

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, db_index=True)


class AssignmentTypeGrade(models.Model):
    """
    Holds student's average grade for each assignment type per course.
    """

    user = models.ForeignKey(User, db_index=True)
    course_id = models.CharField(max_length=255, db_index=True)

    category = models.CharField(max_length=255, db_index=True)
    percent = models.FloatField(db_index=True, null=True)

    class Meta:
        unique_together = (('user', 'course_id', 'category'), )

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, db_index=True)



class AssignmentGrade(models.Model):
    """
    Holds student's assignment grades per course.
    """

    user = models.ForeignKey(User, db_index=True)
    course_id = models.CharField(max_length=255, db_index=True)

    category = models.CharField(max_length=255, db_index=True)
    percent = models.FloatField(db_index=True, null=True)
    label = models.CharField(max_length=32, db_index=True)
    detail = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = (('user', 'course_id', 'label'), )

    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, db_index=True)


class Log(models.Model):
    """
    Log of when a script in this django app was last run. Use to filter out students or rows that don't need to be
    processed in the populate scripts and show instructors how fresh the data is.
    """

    script_id = models.CharField(max_length=255, db_index=True)
    course_id = models.CharField(max_length=255, db_index=True)
    created = models.DateTimeField(null=True, db_index=True)

    class Meta:
        ordering = ["-created"]
        get_latest_by = "created"
