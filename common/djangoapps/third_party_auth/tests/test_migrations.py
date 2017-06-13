"""
Tests potentially haphazard migrations, especially data migrations.
"""

import json

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test.testcases import TransactionTestCase
import social.backends as backends

from third_party_auth.models import SAMLProviderConfig


APP_NAME = 'third_party_auth'
MIGRATIONS = [
    None,
    '0001_initial',
    '0002_schema__provider_icon_image',
    '0003_samlproviderconfig_debug_mode',
    '0004_add_visible_field',
    '0005_add_site_field',
    '0006_samlproviderconfig_automatic_refresh_enabled',
    '0007_auto_20170406_0912',
    '0008_auto_20170413_1455',
    '0009_auto_20170415_1144',
    '0010_add_skip_hinted_login_dialog_field',
    '0011_samlproviderconfig_json_attributes'
]


class MigrationTestCase(TransactionTestCase):
    """A test case for migrations."""

    migrate_from = None
    migrate_to = None
    model = None

    def setUp(self):
        super(MigrationTestCase, self).setUp()
        self.executor = MigrationExecutor(connection)
        self.executor.migrate(self.migrate_from)

    def migrate_to_dest(self):
        self.executor.loader.build_graph()
        self.executor.migrate(self.migrate_to)

    def migrate_to_origin(self):
        self.executor.loader.build_graph()
        self.executor.migrate(self.migrate_from)

    def migrate_to_dest_then_origin(self):
        self.migrate_to_dest()
        self.migrate_to_origin()

    @property
    def old_apps(self):
        return self.executor.loader.project_state(self.migrate_from).apps

    @property
    def new_apps(self):
        return self.executor.loader.project_state(self.migrate_to).apps

    @property
    def model_label(self):
        return self.model._meta.get_field('name')


class SAMLProviderConfigDataMigrationTestCase(MigrationTestCase):
    """
    Tests the migration forwards and backwards between
    0010_add_skip_hinted_login_dialog_field and
    0011_samlprovider_json_attributes.
    """

    backend = backends.saml
    attributes = {
        "attr_permanent_user_id": backend.OID_USERID,
        "attr_fullname": backend.OID_COMMON_NAME,
        "attr_first_name": backend.OID_GIVEN_NAME,
        "attr_last_name": backend.OID_SURNAM,
        "attr_username": backend.OID_USERID,
        "attr_email": backend.OID_MAIL
    }

    base_migration = 10
    migrate_from = [(APP_NAME, MIGRATIONS[base_migration])]
    migrate_to = [(APP_NAME, MIGRATIONS[base_migration + 1])]
    model = SAMLProviderConfig

    def setUp(self):
        super(MigrationTestCase, self).setUp()
        self.old_instance = self.setup_old_samlproviderconfig()
        self.new_instance = self.setup_new_samlproviderconfig()
        self.new_instance_attrs = json.loads(self.new_instance.attributes)

    def tearDown(self):
        super(MigrationTestCase, self).tearDown()
        self.model.objects.all.delete()

    def test_migration_to_json_model(self):
        self.assertEqual(self.old_instance.attr_email, self.backend.OID_MAIL)
        self.old_instance.save()
        self.migrate_to_dest()
        self.assertIsNotNone(
            self.model.objects.filter(
                attributes=json.dumps(self.attributes)
            )
        )
        self.assertIsNone(
            self.model.objects.filter(**self.attributes)
        )

    def test_migration_from_json_model(self):
        self.assertEqual(self.new_instance_attrs['attr_email'], self.backend.OID_MAIL)
        self.new_instance.save()
        self.migrate_to_origin()
        self.assertIsNotNone(
            self.model.objects.all().filter(**self.attributes)
        )
        self.assertIsNone(
            self.model.objects.all().filter(
                attributes=json.dumps(self.attributes)
            )
        )

    def apply_common_configurations(self, **kwargs):
        """Necessities for both data models."""
        kwargs.setdefault('name', 'some_provider_name')
        kwargs.setdefault('idp_slug', 'some-idp-slug')
        kwargs.setdefault('entity_id', 'some_entity_id')
        kwargs.setdefault('metadata_source', 'some_metadata_source')

    def setup_old_samlproviderconfig(self, **kwargs):
        """Sets up version with explicit attribute fields."""
        SAMLProviderConfig = self.old_apps.get_model(APP_NAME, self.model_label)
        self.apply_common_configurations(**kwargs)
        kwargs.update(self.attributes)
        return SAMLProviderConfig(**kwargs)

    def setup_new_samlproviderconfig(self, **kwargs):
        """Sets up version with JSON-based attributes."""
        SAMLProviderConfig = self.new_apps.get_model(APP_NAME, self.model_label)
        self.apply_common_configurations(**kwargs)
        kwargs.setdefault('attributes', json.dumps(self.attributes))
        return SAMLProviderConfig(**kwargs)
