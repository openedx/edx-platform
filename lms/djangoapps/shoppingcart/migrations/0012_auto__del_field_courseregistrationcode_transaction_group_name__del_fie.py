# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'CourseRegistrationCode.transaction_group_name'
        db.delete_column('shoppingcart_courseregistrationcode', 'transaction_group_name')

        # Deleting field 'Invoice.purchaser_contact'
        db.delete_column('shoppingcart_invoice', 'purchaser_contact')

        # Deleting field 'Invoice.purchaser_email'
        db.delete_column('shoppingcart_invoice', 'purchaser_email')

        # Deleting field 'Invoice.reference'
        db.delete_column('shoppingcart_invoice', 'reference')

        # Deleting field 'Invoice.purchaser_name'
        db.delete_column('shoppingcart_invoice', 'purchaser_name')

        # Adding field 'Invoice.company_name'
        db.add_column('shoppingcart_invoice', 'company_name',
                      self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True),
                      keep_default=False)

        # Adding field 'Invoice.course_id'
        db.add_column('shoppingcart_invoice', 'course_id',
                      self.gf('xmodule_django.models.CourseKeyField')(max_length=255, db_index=True),
                      keep_default=False)

        # Adding field 'Invoice.company_contact_name'
        db.add_column('shoppingcart_invoice', 'company_contact_name',
                      self.gf('django.db.models.fields.CharField')(max_length=255),
                      keep_default=False)

        # Adding field 'Invoice.company_contact_email'
        db.add_column('shoppingcart_invoice', 'company_contact_email',
                      self.gf('django.db.models.fields.CharField')(max_length=255),
                      keep_default=False)

        # Adding field 'Invoice.company_reference'
        db.add_column('shoppingcart_invoice', 'company_reference',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True),
                      keep_default=False)

        # Adding field 'Invoice.internal_reference'
        db.add_column('shoppingcart_invoice', 'internal_reference',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'CourseRegistrationCode.transaction_group_name'
        db.add_column('shoppingcart_courseregistrationcode', 'transaction_group_name',
                      self.gf('django.db.models.fields.CharField')(blank=True, max_length=255, null=True, db_index=True),
                      keep_default=False)

        # Adding field 'Invoice.purchaser_contact'
        db.add_column('shoppingcart_invoice', 'purchaser_contact',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255),
                      keep_default=False)

        # Adding field 'Invoice.purchaser_email'
        db.add_column('shoppingcart_invoice', 'purchaser_email',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255),
                      keep_default=False)

        # Adding field 'Invoice.reference'
        db.add_column('shoppingcart_invoice', 'reference',
                      self.gf('django.db.models.fields.CharField')(max_length=255, null=True),
                      keep_default=False)

        # Adding field 'Invoice.purchaser_name'
        db.add_column('shoppingcart_invoice', 'purchaser_name',
                      self.gf('django.db.models.fields.CharField')(default='', max_length=255, db_index=True),
                      keep_default=False)

        # Deleting field 'Invoice.company_name'
        db.delete_column('shoppingcart_invoice', 'company_name')

        # Deleting field 'Invoice.course_id'
        db.delete_column('shoppingcart_invoice', 'course_id')

        # Deleting field 'Invoice.company_contact_name'
        db.delete_column('shoppingcart_invoice', 'company_contact_name')

        # Deleting field 'Invoice.company_contact_email'
        db.delete_column('shoppingcart_invoice', 'company_contact_email')

        # Deleting field 'Invoice.company_reference'
        db.delete_column('shoppingcart_invoice', 'company_reference')

        # Deleting field 'Invoice.internal_reference'
        db.delete_column('shoppingcart_invoice', 'internal_reference')


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
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '128', 'db_index': 'True'}),
            'mode': ('django.db.models.fields.SlugField', [], {'max_length': '50'}),
            'orderitem_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['shoppingcart.OrderItem']", 'unique': 'True', 'primary_key': 'True'})
        },
        'shoppingcart.coupon': {
            'Meta': {'object_name': 'Coupon'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '32', 'db_index': 'True'}),
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 8, 13, 0, 0)'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'percentage_discount': ('django.db.models.fields.IntegerField', [], {'default': '0'})
        },
        'shoppingcart.couponredemption': {
            'Meta': {'object_name': 'CouponRedemption'},
            'coupon': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoppingcart.Coupon']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoppingcart.Order']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'shoppingcart.courseregistrationcode': {
            'Meta': {'object_name': 'CourseRegistrationCode'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '32', 'db_index': 'True'}),
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 8, 13, 0, 0)'}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_by_user'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoppingcart.Invoice']", 'null': 'True'})
        },
        'shoppingcart.invoice': {
            'Meta': {'object_name': 'Invoice'},
            'company_contact_email': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'company_contact_name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'company_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'company_reference': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'internal_reference': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'}),
            'tax_id': ('django.db.models.fields.CharField', [], {'max_length': '64', 'null': 'True'}),
            'total_amount': ('django.db.models.fields.FloatField', [], {})
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
            'refunded_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'cart'", 'max_length': '32'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'shoppingcart.orderitem': {
            'Meta': {'object_name': 'OrderItem'},
            'currency': ('django.db.models.fields.CharField', [], {'default': "'usd'", 'max_length': '8'}),
            'fulfilled_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'line_desc': ('django.db.models.fields.CharField', [], {'default': "'Misc. Item'", 'max_length': '1024'}),
            'list_price': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '30', 'decimal_places': '2'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoppingcart.Order']"}),
            'qty': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'refund_requested_time': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'db_index': 'True'}),
            'report_comments': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'service_fee': ('django.db.models.fields.DecimalField', [], {'default': '0.0', 'max_digits': '30', 'decimal_places': '2'}),
            'status': ('django.db.models.fields.CharField', [], {'default': "'cart'", 'max_length': '32', 'db_index': 'True'}),
            'unit_cost': ('django.db.models.fields.DecimalField', [], {'default': '0.0', 'max_digits': '30', 'decimal_places': '2'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'shoppingcart.paidcourseregistration': {
            'Meta': {'object_name': 'PaidCourseRegistration', '_ormbases': ['shoppingcart.OrderItem']},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '128', 'db_index': 'True'}),
            'mode': ('django.db.models.fields.SlugField', [], {'default': "'honor'", 'max_length': '50'}),
            'orderitem_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['shoppingcart.OrderItem']", 'unique': 'True', 'primary_key': 'True'})
        },
        'shoppingcart.paidcourseregistrationannotation': {
            'Meta': {'object_name': 'PaidCourseRegistrationAnnotation'},
            'annotation': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'unique': 'True', 'max_length': '128', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'shoppingcart.registrationcoderedemption': {
            'Meta': {'object_name': 'RegistrationCodeRedemption'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'order': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoppingcart.Order']"}),
            'redeemed_at': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime(2014, 8, 13, 0, 0)', 'null': 'True'}),
            'redeemed_by': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'registration_code': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['shoppingcart.CourseRegistrationCode']"})
        },
        'student.courseenrollment': {
            'Meta': {'ordering': "('user', 'course_id')", 'unique_together': "(('user', 'course_id'),)", 'object_name': 'CourseEnrollment'},
            'course_id': ('xmodule_django.models.CourseKeyField', [], {'max_length': '255', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'mode': ('django.db.models.fields.CharField', [], {'default': "'honor'", 'max_length': '100'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        }
    }

    complete_apps = ['shoppingcart']