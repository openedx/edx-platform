# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('credit', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='CreditConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('cache_ttl', models.PositiveIntegerField(default=0, help_text='Specified in seconds. Enable caching by setting this to a value greater than 0.', verbose_name='Cache Time To Live')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'ordering': ('-change_date',),
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='creditprovider',
            name='provider_description',
            field=models.TextField(default=b'', help_text='Description for the credit provider displayed to users.'),
        ),
        migrations.AddField(
            model_name='creditprovider',
            name='fulfillment_instructions',
            field=models.TextField(help_text='Plain text or html content for displaying further steps on receipt page *after* paying for the credit to get credit for a credit course against a credit provider.', null=True, blank=True),
        ),
        migrations.AddField(
            model_name='creditprovider',
            name='eligibility_email_message',
            field=models.TextField(default=b'', help_text='Plain text or html content for displaying custom message inside credit eligibility email content which is sent when user has met all credit eligibility requirements.'),
        ),
        migrations.AddField(
            model_name='creditprovider',
            name='receipt_email_message',
            field=models.TextField(default=b'', help_text='Plain text or html content for displaying custom message inside credit receipt email content which is sent *after* paying to get credit for a credit course.'),
        ),
        migrations.AddField(
            model_name='creditprovider',
            name='thumbnail_url',
            field=models.URLField(default=b'', help_text='Thumbnail image url of the credit provider.', max_length=255),
        ),
    ]
