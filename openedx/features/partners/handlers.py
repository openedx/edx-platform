from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.dispatch import receiver
from django.db.models.signals import post_save

from .constants import PERFORMANCE_PERM_FRMT
from .models import Partner


@receiver(post_save, sender=Partner)
def create_partner_performance_permission(sender, instance, created, **kwargs):
    if created:
        slug = instance.slug
        Permission.objects.create(
            codename=PERFORMANCE_PERM_FRMT.format(slug=slug),
            name='Can access {slug} performance'.format(slug=slug),
            content_type=ContentType.objects.get_for_model(Partner)
        )
