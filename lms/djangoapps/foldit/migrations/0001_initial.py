# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Score'
        db.create_table('foldit_score', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='foldit_scores', to=orm['auth.User'])),
            ('unique_user_id', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('puzzle_id', self.gf('django.db.models.fields.IntegerField')()),
            ('best_score', self.gf('django.db.models.fields.FloatField')(db_index=True)),
            ('current_score', self.gf('django.db.models.fields.FloatField')(db_index=True)),
            ('score_version', self.gf('django.db.models.fields.IntegerField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('foldit', ['Score'])

        # Adding model 'PuzzleComplete'
        db.create_table('foldit_puzzlecomplete', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='foldit_puzzles_complete', to=orm['auth.User'])),
            ('unique_user_id', self.gf('django.db.models.fields.CharField')(max_length=50, db_index=True)),
            ('puzzle_id', self.gf('django.db.models.fields.IntegerField')()),
            ('puzzle_set', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('puzzle_subset', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('foldit', ['PuzzleComplete'])

        # Adding unique constraint on 'PuzzleComplete', fields ['user', 'puzzle_id', 'puzzle_set', 'puzzle_subset']
        db.create_unique('foldit_puzzlecomplete', ['user_id', 'puzzle_id', 'puzzle_set', 'puzzle_subset'])


    def backwards(self, orm):
        # Removing unique constraint on 'PuzzleComplete', fields ['user', 'puzzle_id', 'puzzle_set', 'puzzle_subset']
        db.delete_unique('foldit_puzzlecomplete', ['user_id', 'puzzle_id', 'puzzle_set', 'puzzle_subset'])

        # Deleting model 'Score'
        db.delete_table('foldit_score')

        # Deleting model 'PuzzleComplete'
        db.delete_table('foldit_puzzlecomplete')


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
        'foldit.puzzlecomplete': {
            'Meta': {'ordering': "['puzzle_id']", 'unique_together': "(('user', 'puzzle_id', 'puzzle_set', 'puzzle_subset'),)", 'object_name': 'PuzzleComplete'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'puzzle_id': ('django.db.models.fields.IntegerField', [], {}),
            'puzzle_set': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'puzzle_subset': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'unique_user_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'foldit_puzzles_complete'", 'to': "orm['auth.User']"})
        },
        'foldit.score': {
            'Meta': {'object_name': 'Score'},
            'best_score': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'current_score': ('django.db.models.fields.FloatField', [], {'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'puzzle_id': ('django.db.models.fields.IntegerField', [], {}),
            'score_version': ('django.db.models.fields.IntegerField', [], {}),
            'unique_user_id': ('django.db.models.fields.CharField', [], {'max_length': '50', 'db_index': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'foldit_scores'", 'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['foldit']
