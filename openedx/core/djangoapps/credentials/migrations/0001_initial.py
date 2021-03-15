import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CredentialsApiConfig',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('internal_service_url', models.URLField(verbose_name='Internal Service URL')),
                ('public_service_url', models.URLField(verbose_name='Public Service URL')),
                ('enable_learner_issuance', models.BooleanField(default=False, help_text='Enable issuance of credentials via Credential Service.', verbose_name='Enable Learner Issuance')),
                ('enable_studio_authoring', models.BooleanField(default=False, help_text='Enable authoring of Credential Service credentials in Studio.', verbose_name='Enable Authoring of Credential in Studio')),
                ('cache_ttl', models.PositiveIntegerField(default=0, help_text='Specified in seconds. Enable caching by setting this to a value greater than 0.', verbose_name='Cache Time To Live')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'ordering': ('-change_date',),
                'abstract': False,
            },
        ),
    ]
