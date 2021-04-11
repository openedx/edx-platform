# -*- coding: utf-8 -*-


from datetime import datetime

from django.db import migrations, models


def backfill_refundability(apps, schema_editor):
    CourseEntitlementSupportDetail = apps.get_model('entitlements', 'CourseEntitlementSupportDetail')
    for support_detail in CourseEntitlementSupportDetail.objects.all().select_related('entitlement'):
        support_detail.entitlement.refund_locked = True
        support_detail.entitlement.save()


def revert_backfill(apps, schema_editor):
    CourseEntitlementSupportDetail = apps.get_model('entitlements', 'CourseEntitlementSupportDetail')
    for support_detail in CourseEntitlementSupportDetail.objects.all().select_related('entitlement'):
        support_detail.entitlement.refund_locked = False
        support_detail.entitlement.save()


class Migration(migrations.Migration):

    dependencies = [
        ('entitlements', '0009_courseentitlement_refund_locked'),
    ]

    operations = [
        migrations.RunPython(backfill_refundability, revert_backfill),
    ]
