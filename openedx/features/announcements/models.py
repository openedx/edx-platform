"""
Models for Announcements
"""


from django.db import models


class Announcement(models.Model):
<<<<<<< HEAD
    """Site-wide announcements to be displayed on the dashboard"""
=======
    """
    Site-wide announcements to be displayed on the dashboard

    .. no_pii:
    """
>>>>>>> 139b4167b37b49d2d69cccdbd19d8ccef40d3374
    class Meta:
        app_label = 'announcements'

    content = models.CharField(max_length=1000, null=False, default="lorem ipsum")
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.content
