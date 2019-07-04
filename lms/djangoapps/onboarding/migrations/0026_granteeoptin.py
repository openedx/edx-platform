# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings


def add_data(apps, schema_editor):
    PartnerNetwork = apps.get_model('onboarding', 'PartnerNetwork')

    # Mark all Partner Networks to be unaffiliated
    last_order = PartnerNetwork.objects.all().order_by('order').last()

    # Add new Partner Network, Echidna Giving
    PartnerNetwork.objects.create(
        code="ECHIDNA", label="Echidna Giving",
        order=last_order.order + 1 if last_order else 1,
        show_opt_in=True,
        affiliated_name='grantee',
        program_name='Capacity Building Program'
    )


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('onboarding', '0025_registrationtype'),
    ]

    operations = [
        migrations.CreateModel(
            name='GranteeOptIn',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('agreed', models.BooleanField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('organization_partner', models.ForeignKey(related_name='grantee_opt_in', to='onboarding.OrganizationPartner')),
                ('user', models.ForeignKey(related_name='grantee_opt_in', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='historicalorganization',
            name='has_affiliated_partner',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='organization',
            name='has_affiliated_partner',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='partnernetwork',
            name='affiliated_name',
            field=models.CharField(max_length=32, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='partnernetwork',
            name='program_name',
            field=models.CharField(max_length=64, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='partnernetwork',
            name='show_opt_in',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(add_data)
    ]
