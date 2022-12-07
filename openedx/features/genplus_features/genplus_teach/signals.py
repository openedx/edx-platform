import logging
from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from openedx.features.genplus_features.genplus_teach.models import PortfolioEntry, PortfolioReflection, ReflectionAnswer

log = logging.getLogger(__name__)

@receiver(post_save, sender=PortfolioEntry)
@receiver(post_save, sender=ReflectionAnswer)
def create_portfolio_reflection_ans_entry(sender, instance, created, **kwargs):
    """
    Post save handler to create/update PortfolioReflection instances when
    either Portfolio or reflection_answer entry is created/updated
    """
    content_type = ContentType.objects.get_for_model(instance)
    try:
        portfolio_reflection = PortfolioReflection.objects.get(content_type=content_type, object_id=instance.id)
    except PortfolioReflection.DoesNotExist:
        portfolio_reflection = PortfolioReflection(content_type=content_type, object_id=instance.id)
        portfolio_reflection.save()


@receiver(post_delete, sender=PortfolioEntry)
@receiver(post_delete, sender=ReflectionAnswer)
def delete_portfolio_reflection_ans_entry(sender, instance, *args, **kwargs):
    """
    Post delete handler to delete PortfolioReflection instances when
    either Portfolio or reflection_answer entry is deleted
    """
    content_type = ContentType.objects.get_for_model(instance)
    try:
        portfolio_reflection = PortfolioReflection.objects.get(content_type=content_type, object_id=instance.id)
        portfolio_reflection.delete()
    except PortfolioReflection.DoesNotExist:
        pass
