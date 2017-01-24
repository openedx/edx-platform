"""
Django Model for tags
"""
from django.db import models


class TagCategories(models.Model):
    """
    This model represents tag categories.
    """
    name = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)

    class Meta(object):
        app_label = "tagging"
        ordering = ('title',)

    def __unicode__(self):
        return "[TagCategories] {}: {}".format(self.name, self.title)

    def get_values(self):
        """
        Return the list of available values for the particular category
        """
        return [t.value for t in TagAvailableValues.objects.filter(category=self)]


class TagAvailableValues(models.Model):
    """
    This model represents available values for tags.
    """
    category = models.ForeignKey(TagCategories, db_index=True)
    value = models.CharField(max_length=255)

    class Meta(object):
        app_label = "tagging"
        ordering = ('id',)

    def __unicode__(self):
        return "[TagAvailableValues] {}: {}".format(self.category, self.value)
