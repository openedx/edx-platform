"""
Django Model for tags
"""


from django.db import models


class TagCategories(models.Model):
    """
    This model represents tag categories.

    .. no_pii:
    """
    name = models.CharField(max_length=255, unique=True)
    title = models.CharField(max_length=255)

    class Meta:
        app_label = "tagging"
        ordering = ('title',)
        verbose_name = "tag category"
        verbose_name_plural = "tag categories"

    def __str__(self):
        return f"[TagCategories] {self.name}: {self.title}"

    def get_values(self):
        """
        Return the list of available values for the particular category
        """
        return [t.value for t in TagAvailableValues.objects.filter(category=self)]


class TagAvailableValues(models.Model):
    """
    This model represents available values for tags.

    .. no_pii:
    """
    category = models.ForeignKey(TagCategories, db_index=True, on_delete=models.CASCADE)
    value = models.CharField(max_length=255)

    class Meta:
        app_label = "tagging"
        ordering = ('id',)
        verbose_name = "available tag value"

    def __str__(self):
        return f"[TagAvailableValues] {self.category}: {self.value}"
