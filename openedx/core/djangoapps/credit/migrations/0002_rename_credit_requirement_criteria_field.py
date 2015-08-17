# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'CreditRequirement.configuration'
        db.delete_column('credit_creditrequirement', 'configuration')

        # Adding field 'CreditRequirement.criteria'
        db.add_column('credit_creditrequirement', 'criteria',
                      self.gf('jsonfield.fields.JSONField')(default=''),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'CreditRequirement.configuration'
        db.add_column('credit_creditrequirement', 'configuration',
                      self.gf('jsonfield.fields.JSONField')(default=''),
                      keep_default=False)

        # Deleting field 'CreditRequirement.criteria'
        db.delete_column('credit_creditrequirement', 'criteria')


    models = {
        'credit.creditcourse': {
            'Meta': {'object_name': 'CreditCourse'},
            'course_key': ('xmodule_django.models.CourseKeyField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'credit.crediteligibility': {
            'Meta': {'unique_together': "(('username', 'course'),)", 'object_name': 'CreditEligibility'},
            'course': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'eligibilities'", 'to': "orm['credit.CreditCourse']"}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'provider': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'eligibilities'", 'to': "orm['credit.CreditProvider']"}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'credit.creditprovider': {
            'Meta': {'object_name': 'CreditProvider'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'display_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'provider_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255', 'db_index': 'True'})
        },
        'credit.creditrequirement': {
            'Meta': {'unique_together': "(('namespace', 'name', 'course'),)", 'object_name': 'CreditRequirement'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'course': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credit_requirements'", 'to': "orm['credit.CreditCourse']"}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'criteria': ('jsonfield.fields.JSONField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'namespace': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'credit.creditrequirementstatus': {
            'Meta': {'object_name': 'CreditRequirementStatus'},
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('model_utils.fields.AutoLastModifiedField', [], {'default': 'datetime.datetime.now'}),
            'requirement': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'statuses'", 'to': "orm['credit.CreditRequirement']"}),
            'status': ('django.db.models.fields.CharField', [], {'max_length': '32'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        }
    }

    complete_apps = ['credit']