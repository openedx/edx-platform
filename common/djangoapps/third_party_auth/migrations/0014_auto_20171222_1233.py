# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0013_sync_learner_profile_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ltiproviderconfig',
            name='drop_existing_session',
        ),
        migrations.RemoveField(
            model_name='oauth2providerconfig',
            name='drop_existing_session',
        ),
        migrations.RemoveField(
            model_name='samlproviderconfig',
            name='drop_existing_session',
        ),
    ]
