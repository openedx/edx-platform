"""
handler methods for applications
"""

from django.contrib.auth.models import Group
from django.db.models.signals import post_delete, pre_save
from django.dispatch import receiver

from .models import BusinessLine


@receiver(pre_save, sender=BusinessLine)
def update_business_line_group(instance, **kwargs):  # pylint: disable=unused-argument
    """
    Add user group on creating a Business Line
    Modify user group on updating a Business Line
    """
    if instance.pk is None:
        instance.group = Group.objects.create(name=instance.title)
    else:
        old_instance = BusinessLine.objects.get(pk=instance.pk)
        if old_instance.title != instance.title:
            instance.group.name = instance.title
            instance.group.save()


@receiver(post_delete, sender=BusinessLine)
def delete_business_line_group(instance, **kwargs):  # pylint: disable=unused-argument
    """
    Delete user group on deleting a Business Line
    """
    # TODO: Use instance.group.delete(), once LP-2479 is deployed on prod.
    Group.objects.filter(name=instance.title).delete()
