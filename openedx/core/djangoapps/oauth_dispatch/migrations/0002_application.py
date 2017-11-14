# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

import oauth2_provider.generators
import oauth2_provider.validators
from django.conf import settings
from django.db import connection, migrations, models

log = logging.getLogger(__name__)


class FakeForwardCreateModel(migrations.CreateModel):
    """
    Migration class that only executes forwards if the table does not exist.

    This migration will only be executed for new installations. The table will already exist for installations setup
    prior to this migration being merged. We use the existence of the table to determine if a prior migration applied.
    """

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        model = to_state.apps.get_model(app_label, self.name)
        if self.allow_migrate_model(schema_editor.connection.alias, model):
            # We only migrate if the table does not exist
            table_name = model._meta.db_table
            if table_name in connection.introspection.table_names():
                log.warning(
                    'The database table (%s) for the model %s.%s already exists. No changes have been made to the '
                    'table as this behavior is expected for older installations. This is message is just an FYI that '
                    'this migration has essentially been faked.',
                    table_name, app_label, self.name)
            else:
                schema_editor.create_model(model)


class Migration(migrations.Migration):
    run_before = [
        ('oauth2_provider', '0001_initial'),
    ]

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('oauth_dispatch', '0001_initial'),
    ]

    operations = [
        FakeForwardCreateModel(
            name='Application',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('client_id', models.CharField(default=oauth2_provider.generators.generate_client_id, unique=True, max_length=100, db_index=True)),
                ('redirect_uris', models.TextField(help_text='Allowed URIs list, space separated', blank=True, validators=[oauth2_provider.validators.validate_uris])),
                ('client_type', models.CharField(max_length=32, choices=[('confidential', 'Confidential'), ('public', 'Public')])),
                ('authorization_grant_type', models.CharField(max_length=32, choices=[('authorization-code', 'Authorization code'), ('implicit', 'Implicit'), ('password', 'Resource owner password-based'), ('client-credentials', 'Client credentials')])),
                ('client_secret', models.CharField(default=oauth2_provider.generators.generate_client_secret, max_length=255, db_index=True, blank=True)),
                ('name', models.CharField(max_length=255, blank=True)),
                ('skip_authorization', models.BooleanField(default=False)),
                ('user', models.ForeignKey(related_name='oauth_dispatch_application', blank=True, to=settings.AUTH_USER_MODEL, null=True)),
            ],
            options={
                'db_table': 'oauth2_provider_application',
            },
        ),
    ]
