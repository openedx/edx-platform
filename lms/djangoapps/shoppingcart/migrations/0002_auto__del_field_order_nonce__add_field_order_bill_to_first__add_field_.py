# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'Order.nonce'
        db.delete_column('shoppingcart_order', 'nonce')

        # Adding field 'Order.bill_to_first'
        db.add_column('shoppingcart_order', 'bill_to_first',
                      self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Order.bill_to_last'
        db.add_column('shoppingcart_order', 'bill_to_last',
                      self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Order.bill_to_street1'
        db.add_column('shoppingcart_order', 'bill_to_street1',
                      self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Order.bill_to_street2'
        db.add_column('shoppingcart_order', 'bill_to_street2',
                      self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Order.bill_to_city'
        db.add_column('shoppingcart_order', 'bill_to_city',
                      self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Order.bill_to_postalcode'
        db.add_column('shoppingcart_order', 'bill_to_postalcode',
                      self.gf('django.db.models.fields.CharField')(max_length=16, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Order.bill_to_country'
        db.add_column('shoppingcart_order', 'bill_to_country',
                      self.gf('django.db.models.fields.CharField')(max_length=64, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Order.bill_to_ccnum'
        db.add_column('shoppingcart_order', 'bill_to_ccnum',
                      self.gf('django.db.models.fields.CharField')(max_length=8, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Order.bill_to_cardtype'
        db.add_column('shoppingcart_order', 'bill_to_cardtype',
                      self.gf('django.db.models.fields.CharField')(max_length=32, null=True, blank=True),
                      keep_default=False)

        # Adding field 'Order.processor_reply_dump'
        db.add_column('shoppingcart_order', 'processor_reply_dump',
                      self.gf('django.db.models.fields.TextField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'OrderItem.currency'
        db.add_column('shoppingcart_orderitem', 'currency',
                      self.gf('django.db.models.fields.CharField')(default='usd', max_length=8),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'Order.nonce'
        db.add_column('shoppingcart_order', 'nonce',
                      self.gf('django.db.models.fields.CharField')(default='defaultNonce', max_length=128),
                      keep_default=False)

        # Deleting field 'Order.bill_to_first'
        db.delete_column('shoppingcart_order', 'bill_to_first')

        # Deleting field 'Order.bill_to_last'
        db.delete_column('shoppingcart_order', 'bill_to_last')

        # Deleting field 'Order.bill_to_street1'
        db.delete_column('shoppingcart_order', 'bill_to_street1')

        # Deleting field 'Order.bill_to_street2'
        db.delete_column('shoppingcart_order', 'bill_to_street2')

        # Deleting field 'Order.bill_to_city'
        db.delete_column('shoppingcart_order', 'bill_to_city')

        # Deleting field 'Order.bill_to_postalcode'
        db.delete_column('shoppingcart_order', 'bill_to_postalcode')

        # Deleting field 'Order.bill_to_country'
        db.delete_column('shoppingcart_order', 'bill_to_country')

        # Deleting field 'Order.bill_to_ccnum'
        db.delete_column('shoppingcart_order', 'bill_to_ccnum')

        # Deleting field 'Order.bill_to_cardtype'
        db.delete_column('shoppingcart_order', 'bill_to_cardtype')

        # Deleting field 'Order.processor_reply_dump'
        db.delete_column('shoppingcart_order', 'processor_reply_dump')

        # Deleting field 'OrderItem.currency'
        db.delete_column('shoppingcart_orderitem', 'currency')


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
        'shoppingcart.order': {
            'Meta': {'object_name': 'Order'},
            'bill_to_cardtype': ('django.db.models.fields.CharField', [], {'max_length': '32', 'null': 'True', 'blank': 'True'}),
            'bill_to_ccnum': ('django.db.models.fields.CharField', [], {'max_length': '8', 'null': 'True', 'blank': 'True'}),
            'bill_to_city': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'bill_to_country': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'bill_to_first': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'bill_to_last': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True', 'blank': 'True'}),
            'bill_to_postalcode': ('django.db.models.fields.CharField', [], {'max_length': '16', 'null': 'True', 'blank': 'True'}),
            'bill_to_street1': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'bill_to_street2': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'processor_reply_dump': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'purchase_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'cart'", 'max_length': '32'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'shoppingcart.orderitem': {
            'Meta': {'object_name': 'OrderItem'},
            'currency': ('django.db.models.fields.CharField', [], {'default': "'usd'", 'max_length': '8'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line_cost': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'line_desc': ('django.db.models.fields.CharField', [], {'default': "'Misc. Item'", 'max_length': '1024'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoppingcart.Order']"}),
            'qty': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'cart'", 'max_length': '32'}),
            'unit_cost': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'shoppingcart.paidcourseregistration': {
            'Meta': {'object_name': 'PaidCourseRegistration', '_ormbases': ['shoppingcart.OrderItem']},
            'course_id': ('django.db.models.fields.CharField', [], {'max_length': '128', 'db_index': 'True'}),
            'orderitem_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['shoppingcart.OrderItem']", 'unique': 'True', 'primary_key': 'True'})
        }
    }

    complete_apps = ['shoppingcart']