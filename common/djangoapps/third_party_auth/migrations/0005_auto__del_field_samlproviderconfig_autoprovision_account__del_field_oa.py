# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'SAMLProviderConfig.autoprovision_account'
        db.delete_column('third_party_auth_samlproviderconfig', 'autoprovision_account')

        # Deleting field 'OAuth2ProviderConfig.autoprovision_account'
        db.delete_column('third_party_auth_oauth2providerconfig', 'autoprovision_account')


    def backwards(self, orm):
        # Adding field 'SAMLProviderConfig.autoprovision_account'
        db.add_column('third_party_auth_samlproviderconfig', 'autoprovision_account',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)

        # Adding field 'OAuth2ProviderConfig.autoprovision_account'
        db.add_column('third_party_auth_oauth2providerconfig', 'autoprovision_account',
                      self.gf('django.db.models.fields.BooleanField')(default=False),
                      keep_default=False)


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'third_party_auth.oauth2providerconfig': {
            'Meta': {'object_name': 'OAuth2ProviderConfig'},
            'backend_name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'change_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'changed_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'icon_class': ('django.db.models.fields.CharField', [], {'default': "'fa-sign-in'", 'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'other_settings': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'secondary': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'secret': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'skip_email_verification': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'skip_registration_form': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'third_party_auth.samlconfiguration': {
            'Meta': {'object_name': 'SAMLConfiguration'},
            'change_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'changed_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'entity_id': ('django.db.models.fields.CharField', [], {'default': "'http://saml.example.com'", 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'org_info_str': ('django.db.models.fields.TextField', [], {'default': '\'{"en-US": {"url": "http://www.example.com", "displayname": "Example Inc.", "name": "example"}}\''}),
            'other_config_str': ('django.db.models.fields.TextField', [], {'default': '\'{\\n"SECURITY_CONFIG": {"metadataCacheDuration": 604800, "signMetadata": false}\\n}\''}),
            'private_key': ('django.db.models.fields.TextField', [], {}),
            'public_key': ('django.db.models.fields.TextField', [], {})
        },
        'third_party_auth.samlproviderconfig': {
            'Meta': {'object_name': 'SAMLProviderConfig'},
            'attr_email': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'attr_first_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'attr_full_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'attr_last_name': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'attr_user_permanent_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'attr_username': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'backend_name': ('django.db.models.fields.CharField', [], {'default': "'tpa-saml'", 'max_length': '50'}),
            'change_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'changed_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'on_delete': 'models.PROTECT'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'entity_id': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'icon_class': ('django.db.models.fields.CharField', [], {'default': "'fa-sign-in'", 'max_length': '50'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idp_slug': ('django.db.models.fields.SlugField', [], {'max_length': '30'}),
            'metadata_source': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'}),
            'other_settings': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'secondary': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'skip_email_verification': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'skip_registration_form': ('django.db.models.fields.BooleanField', [], {'default': 'False'})
        },
        'third_party_auth.samlproviderdata': {
            'Meta': {'ordering': "('-fetched_at',)", 'object_name': 'SAMLProviderData'},
            'entity_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'expires_at': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'fetched_at': ('django.db.models.fields.DateTimeField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'public_key': ('django.db.models.fields.TextField', [], {}),
            'sso_url': ('django.db.models.fields.URLField', [], {'max_length': '200'})
        }
    }

    complete_apps = ['third_party_auth']