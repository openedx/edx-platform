# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('third_party_auth', '0012_auto_20170626_1135'),
    ]

    operations = [
        migrations.AddField(
            model_name='ltiproviderconfig',
            name='sync_learner_profile_data',
            field=models.BooleanField(default=False, help_text='Synchronize user profile data received from the identity provider with the edX user account on each SSO login. The user will be notified if the email address associated with their account is changed as a part of this synchronization.'),
        ),
        migrations.AddField(
            model_name='oauth2providerconfig',
            name='sync_learner_profile_data',
            field=models.BooleanField(default=False, help_text='Synchronize user profile data received from the identity provider with the edX user account on each SSO login. The user will be notified if the email address associated with their account is changed as a part of this synchronization.'),
        ),
        migrations.AddField(
            model_name='samlproviderconfig',
            name='sync_learner_profile_data',
            field=models.BooleanField(default=False, help_text='Synchronize user profile data received from the identity provider with the edX user account on each SSO login. The user will be notified if the email address associated with their account is changed as a part of this synchronization.'),
        ),
    ]
