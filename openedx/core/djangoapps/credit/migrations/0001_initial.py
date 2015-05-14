# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'CreditCourse'
        db.create_table('credit_creditcourse', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('course_key', self.gf('xmodule_django.models.CourseKeyField')(unique=True, max_length=255, db_index=True)),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('credit', ['CreditCourse'])

        # Adding model 'CreditProvider'
        db.create_table('credit_creditprovider', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('provider_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255, db_index=True)),
            ('display_name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('credit', ['CreditProvider'])

        # Adding model 'CreditRequirement'
        db.create_table('credit_creditrequirement', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(related_name='credit_requirements', to=orm['credit.CreditCourse'])),
            ('namespace', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('configuration', self.gf('jsonfield.fields.JSONField')()),
            ('active', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('credit', ['CreditRequirement'])

        # Adding unique constraint on 'CreditRequirement', fields ['namespace', 'name', 'course']
        db.create_unique('credit_creditrequirement', ['namespace', 'name', 'course_id'])

        # Adding model 'CreditRequirementStatus'
        db.create_table('credit_creditrequirementstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('requirement', self.gf('django.db.models.fields.related.ForeignKey')(related_name='statuses', to=orm['credit.CreditRequirement'])),
            ('status', self.gf('django.db.models.fields.CharField')(max_length=32)),
        ))
        db.send_create_signal('credit', ['CreditRequirementStatus'])

        # Adding model 'CreditEligibility'
        db.create_table('credit_crediteligibility', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('model_utils.fields.AutoCreatedField')(default=datetime.datetime.now)),
            ('modified', self.gf('model_utils.fields.AutoLastModifiedField')(default=datetime.datetime.now)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('course', self.gf('django.db.models.fields.related.ForeignKey')(related_name='eligibilities', to=orm['credit.CreditCourse'])),
            ('provider', self.gf('django.db.models.fields.related.ForeignKey')(related_name='eligibilities', to=orm['credit.CreditProvider'])),
        ))
        db.send_create_signal('credit', ['CreditEligibility'])

        # Adding unique constraint on 'CreditEligibility', fields ['username', 'course']
        db.create_unique('credit_crediteligibility', ['username', 'course_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'CreditEligibility', fields ['username', 'course']
        db.delete_unique('credit_crediteligibility', ['username', 'course_id'])

        # Removing unique constraint on 'CreditRequirement', fields ['namespace', 'name', 'course']
        db.delete_unique('credit_creditrequirement', ['namespace', 'name', 'course_id'])

        # Deleting model 'CreditCourse'
        db.delete_table('credit_creditcourse')

        # Deleting model 'CreditProvider'
        db.delete_table('credit_creditprovider')

        # Deleting model 'CreditRequirement'
        db.delete_table('credit_creditrequirement')

        # Deleting model 'CreditRequirementStatus'
        db.delete_table('credit_creditrequirementstatus')

        # Deleting model 'CreditEligibility'
        db.delete_table('credit_crediteligibility')


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
            'configuration': ('jsonfield.fields.JSONField', [], {}),
            'course': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'credit_requirements'", 'to': "orm['credit.CreditCourse']"}),
            'created': ('model_utils.fields.AutoCreatedField', [], {'default': 'datetime.datetime.now'}),
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
