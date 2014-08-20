"""
Model to define the progress of the course.
"""
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

log = logging.getLogger("models.progressmodules")


class ProgressModules(models.Model):
    """Model to define the progress of the course."""
    SORT_LIST = [
        "progress_module", "display_name", "created", "course_id",
        "module_type", "count", "max_score", "total_score", "submit_count",
        "weight", "start", "due", "correct_map", "student_answers"
    ]
    location = models.CharField(max_length=255, db_index=True, primary_key=True)
    course_id = models.CharField(max_length=255, db_index=True)
    created = models.DateTimeField(auto_now=True)
    display_name = models.CharField(max_length=255)
    module_type = models.CharField(max_length=255, default="problem")
    count = models.IntegerField(default=0)
    max_score = models.FloatField(default=0.0)
    total_score = models.FloatField(default=0.0)
    submit_count = models.IntegerField(default=0)
    weight = models.FloatField(null=True)
    start = models.DateTimeField(null=True)
    due = models.DateTimeField(null=True)
    correct_map = models.TextField(null=True)
    student_answers = models.TextField(null=True)
    mean = models.FloatField(null=True)
    median = models.FloatField(null=True)
    variance = models.FloatField(null=True)
    standard_deviation = models.FloatField(null=True)

    class Meta:
        db_table = "progress_modules"

    def __repr__(self):
        return ("[ProgressModules] {}").format(self.location)

    def __unicode__(self):
        return unicode(repr(self))

    @classmethod
    def get_by_course_id(cls, course_id):
        modules_dict = {}
        modules = cls.objects.filter(course_id=course_id).values()
        for module in modules:
            location = module.pop('location')
            modules_dict[location] = module

        return modules_dict


class ProgressModulesHistory(models.Model):
    """Model to define the history of the ProgressModules."""
    progress_module = models.ForeignKey(ProgressModules, db_index=True)
    created = models.DateTimeField(db_index=True)
    display_name = models.CharField(max_length=255)
    count = models.IntegerField()
    max_score = models.FloatField()
    total_score = models.FloatField()
    submit_count = models.IntegerField()
    weight = models.FloatField(null=True)
    start = models.DateTimeField(null=True)
    due = models.DateTimeField(null=True)
    correct_map = models.TextField(null=True)
    student_answers = models.TextField(null=True)
    mean = models.FloatField(null=True)
    median = models.FloatField(null=True)
    variance = models.FloatField(null=True)
    standard_deviation = models.FloatField(null=True)

    class Meta:
        ordering = ["-created", "progress_module"]
        db_table = "progress_modules_history"

    def __repr__(self):
        return ("{} : created {}").format(
            self.progress_module, self.created)

    def __unicode__(self):
        return unicode(repr(self))

    @receiver(post_save, sender=ProgressModules)
    def save_history(sender, instance, **kwargs):
        """Save a table in trigger with post_save signal."""
        history_entry = ProgressModulesHistory(
            progress_module=instance, created=instance.created,
            display_name=instance.display_name, count=instance.count,
            max_score=instance.max_score, total_score=instance.total_score,
            submit_count=instance.submit_count, weight=instance.weight,
            start=instance.start, due=instance.due,
            correct_map=instance.correct_map,
            student_answers=instance.student_answers
        )
        history_entry.save()
