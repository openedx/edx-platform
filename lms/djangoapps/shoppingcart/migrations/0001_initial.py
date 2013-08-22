# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Order'
        db.create_table('shoppingcart_order', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('currency', self.gf('django.db.models.fields.CharField')(default='usd', max_length=8)),
            ('status', self.gf('django.db.models.fields.CharField')(default='cart', max_length=32)),
            ('purchase_time', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('bill_to_first', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('bill_to_last', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('bill_to_street1', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('bill_to_street2', self.gf('django.db.models.fields.CharField')(max_length=128, blank=True)),
            ('bill_to_city', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('bill_to_state', self.gf('django.db.models.fields.CharField')(max_length=8, blank=True)),
            ('bill_to_postalcode', self.gf('django.db.models.fields.CharField')(max_length=16, blank=True)),
            ('bill_to_country', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('bill_to_ccnum', self.gf('django.db.models.fields.CharField')(max_length=8, blank=True)),
            ('bill_to_cardtype', self.gf('django.db.models.fields.CharField')(max_length=32, blank=True)),
            ('processor_reply_dump', self.gf('django.db.models.fields.TextField')(blank=True)),
        ))
        db.send_create_signal('shoppingcart', ['Order'])

        # Adding model 'OrderItem'
        db.create_table('shoppingcart_orderitem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('order', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['shoppingcart.Order'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('status', self.gf('django.db.models.fields.CharField')(default='cart', max_length=32)),
            ('qty', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('unit_cost', self.gf('django.db.models.fields.DecimalField')(default=0.0, max_digits=30, decimal_places=2)),
            ('line_cost', self.gf('django.db.models.fields.DecimalField')(default=0.0, max_digits=30, decimal_places=2)),
            ('line_desc', self.gf('django.db.models.fields.CharField')(default='Misc. Item', max_length=1024)),
            ('currency', self.gf('django.db.models.fields.CharField')(default='usd', max_length=8)),
        ))
        db.send_create_signal('shoppingcart', ['OrderItem'])

        # Adding model 'PaidCourseRegistration'
        db.create_table('shoppingcart_paidcourseregistration', (
            ('orderitem_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['shoppingcart.OrderItem'], unique=True, primary_key=True)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=128, db_index=True)),
        ))
        db.send_create_signal('shoppingcart', ['PaidCourseRegistration'])

        # Adding model 'CertificateItem'
        db.create_table('shoppingcart_certificateitem', (
            ('orderitem_ptr', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['shoppingcart.OrderItem'], unique=True, primary_key=True)),
            ('course_id', self.gf('django.db.models.fields.CharField')(max_length=128, db_index=True)),
            ('course_enrollment', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['student.CourseEnrollment'])),
            ('mode', self.gf('django.db.models.fields.SlugField')(max_length=50)),
        ))
        db.send_create_signal('shoppingcart', ['CertificateItem'])

    def backwards(self, orm):
        # Deleting model 'Order'
        db.delete_table('shoppingcart_order')

        # Deleting model 'OrderItem'
        db.delete_table('shoppingcart_orderitem')

        # Deleting model 'PaidCourseRegistration'
        db.delete_table('shoppingcart_paidcourseregistration')

        # Deleting model 'CertificateItem'
        db.delete_table('shoppingcart_certificateitem')

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
        'shoppingcart.certificateitem': {
            'Meta': {'object_name': 'CertificateItem', '_ormbases': ['shoppingcart.OrderItem']},
            'course_enrollment': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['student.CourseEnrollment']"}),
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'mode': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'orderitem_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['shoppingcart.OrderItem']", 'unique': 'True', 'primary_key': 'True'})
        },
        'shoppingcart.order': {
            'Meta': {'object_name': 'Order'},
            'bill_to_cardtype': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'bill_to_ccnum': ('django.db.models.fields.CharField', [], {'max_length': '8', 'blank': 'True'}),
            'bill_to_city': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'bill_to_country': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'bill_to_first': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'bill_to_last': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'bill_to_postalcode': ('django.db.models.fields.CharField', [], {'max_length': '16', 'blank': 'True'}),
            'bill_to_state': ('django.db.models.fields.CharField', [], {'max_length': '8', 'blank': 'True'}),
            'bill_to_street1': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'bill_to_street2': ('django.db.models.fields.CharField', [], {'max_length': '128', 'blank': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'usd'", 'max_length': '8'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'processor_reply_dump': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'purchase_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'cart'", 'max_length': '32'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'shoppingcart.orderitem': {
            'Meta': {'object_name': 'OrderItem'},
            'currency': ('django.db.models.fields.CharField', [], {'default': "'usd'", 'max_length': '8'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line_cost': ('django.db.models.fields.DecimalField', [], {'default': '0.0', 'max_digits': '30', 'decimal_places': '2'}),
            'line_desc': ('django.db.models.fields.CharField', [], {'default': "'Misc. Item'", 'max_length': '1024'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoppingcart.Order']"}),
            'qty': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'cart'", 'max_length': '32'}),
            'unit_cost': ('django.db.models.fields.DecimalField', [], {'default': '0.0', 'max_digits': '30', 'decimal_places': '2'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'shoppingcart.paidcourseregistration': {
            'Meta': {'object_name': 'PaidCourseRegistration', '_ormbases': ['shoppingcart.OrderItem']},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'orderitem_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['shoppingcart.OrderItem']", 'unique': 'True', 'primary_key': 'True'})
        },
        'student.courseenrollment': {
            'Meta': {'ordering': "('user', 'course_id')", 'unique_together': "(('user', 'course_id'),)", 'object_name': 'CourseEnrollment'},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'mode': ('django.db.models.fields.CharField', [], {'default': "'honor'", 'max_length': '100'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['shoppingcart']
