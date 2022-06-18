from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from waffle import get_waffle_flag_model


@receiver(m2m_changed, sender=get_waffle_flag_model().users.through)
@receiver(m2m_changed, sender=get_waffle_flag_model().groups.through)
def flag_membership_changed(sender, instance, action, **kwargs):
    if action in ('post_add', 'post_remove'):
        flag_model = get_waffle_flag_model()

        # instance could be a flag or an instance of the related model
        # https://docs.djangoproject.com/en/dev/ref/signals/#m2m-changed
        if isinstance(instance, flag_model):
            instance.flush()
        else:
            for flag in flag_model.objects.filter(pk__in=kwargs['pk_set']):
                flag.flush()
