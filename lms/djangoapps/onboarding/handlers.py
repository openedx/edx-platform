"""
Handlers for onboarding app
"""
from django.db import connection

from django.contrib.auth.models import User
from django.db.models.signals import post_delete
from django.dispatch import receiver


@receiver(post_delete, sender=User)
def delete_all_user_data(sender, instance, **kwargs):

    cursor = connection.cursor()

    cursor.execute(
        'DELETE FROM auth_historicaluser WHERE id={};'.format(instance.id))
    cursor.execute(
        'DELETE FROM auth_historicaluserprofile WHERE user_id={};'.format(instance.id))
    cursor.execute(
        'DELETE FROM onboarding_historicaluserextendedprofile WHERE user_id={};'.format(instance.id))
    cursor.execute(
        'UPDATE onboarding_organization SET unclaimed_org_admin_email=NULL WHERE unclaimed_org_admin_email="{}"'.format(instance.email))
    cursor.execute(
        'UPDATE onboarding_organization SET alternate_admin_email=NULL WHERE alternate_admin_email="{}"'.format(instance.email))
    cursor.execute(
        'DELETE FROM onboarding_historicalorganization WHERE unclaimed_org_admin_email="{}" OR alternate_admin_email="{}"'.format(instance.email, instance.email))
