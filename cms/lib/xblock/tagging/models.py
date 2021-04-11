"""
Django Model for tags
"""


from django.db import models
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class TagCategories(models.Model):
    """
    This model represents tag categories.

    .. no_pii:
    """
    name = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)

    class Meta(object):
        app_label = "tagging"
        ordering = ('title',)
        verbose_name = "tag category"
        verbose_name_plural = "tag categories"

    def __str__(self):
        return "[TagCategories] {}: {}".format(self.name, self.title)

    def get_values(self):
        """
        Return the list of available values for the particular category
        """
        return [t.value for t in TagAvailableValues.objects.filter(category=self)]


@python_2_unicode_compatible
class TagAvailableValues(models.Model):
    """
    This model represents available values for tags.

    .. no_pii:
    """
    category = models.ForeignKey(TagCategories, db_index=True, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    class Meta(object):
        app_label = "tagging"
        ordering = ('id',)
        verbose_name = "available tag value"

    def __str__(self):
        return "[TagAvailableValues] {}: {}".format(self.category, self.value)
