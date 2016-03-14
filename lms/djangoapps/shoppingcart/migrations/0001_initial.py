# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import django.db.models.deletion
from django.conf import settings
import model_utils.fields
import xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('student', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Coupon',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(max_length=32, db_index=True)),
                ('description', models.CharField(max_length=255, null=True, blank=True)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255)),
                ('percentage_discount', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('expiration_date', models.DateTimeField(null=True, blank=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CouponRedemption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('coupon', models.ForeignKey(to='shoppingcart.Coupon')),
            ],
        ),
        migrations.CreateModel(
            name='CourseRegCodeItemAnnotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', xmodule_django.models.CourseKeyField(unique=True, max_length=128, db_index=True)),
                ('annotation', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CourseRegistrationCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=32, db_index=True)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('mode_slug', models.CharField(max_length=100, null=True)),
                ('is_valid', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(related_name='created_by_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='DonationConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'ordering': ('-change_date',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('company_name', models.CharField(max_length=255, db_index=True)),
                ('company_contact_name', models.CharField(max_length=255)),
                ('company_contact_email', models.CharField(max_length=255)),
                ('recipient_name', models.CharField(max_length=255)),
                ('recipient_email', models.CharField(max_length=255)),
                ('address_line_1', models.CharField(max_length=255)),
                ('address_line_2', models.CharField(max_length=255, null=True, blank=True)),
                ('address_line_3', models.CharField(max_length=255, null=True, blank=True)),
                ('city', models.CharField(max_length=255, null=True)),
                ('state', models.CharField(max_length=255, null=True)),
                ('zip', models.CharField(max_length=15, null=True)),
                ('country', models.CharField(max_length=64, null=True)),
                ('total_amount', models.FloatField()),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('internal_reference', models.CharField(help_text='Internal reference code for this invoice.', max_length=255, null=True, blank=True)),
                ('customer_reference_number', models.CharField(help_text="Customer's reference code for this invoice.", max_length=63, null=True, blank=True)),
                ('is_valid', models.BooleanField(default=True)),
            ],
        ),
        migrations.CreateModel(
            name='InvoiceHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('snapshot', models.TextField(blank=True)),
                ('invoice', models.ForeignKey(to='shoppingcart.Invoice')),
            ],
            options={
                'get_latest_by': 'timestamp',
            },
        ),
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('qty', models.IntegerField(default=1, help_text='The number of items sold.')),
                ('unit_price', models.DecimalField(default=0.0, help_text='The price per item sold, including discounts.', max_digits=30, decimal_places=2)),
                ('currency', models.CharField(default=b'usd', help_text='Lower-case ISO currency codes', max_length=8)),
            ],
        ),
        migrations.CreateModel(
            name='InvoiceTransaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('amount', models.DecimalField(default=0.0, help_text='The amount of the transaction.  Use positive amounts for payments and negative amounts for refunds.', max_digits=30, decimal_places=2)),
                ('currency', models.CharField(default=b'usd', help_text='Lower-case ISO currency codes', max_length=8)),
                ('comments', models.TextField(help_text='Optional: provide additional information for this transaction', null=True, blank=True)),
                ('status', models.CharField(default=b'started', help_text="The status of the payment or refund. 'started' means that payment is expected, but money has not yet been transferred. 'completed' means that the payment or refund was received. 'cancelled' means that payment or refund was expected, but was cancelled before money was transferred. ", max_length=32, choices=[(b'started', b'started'), (b'completed', b'completed'), (b'cancelled', b'cancelled')])),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('invoice', models.ForeignKey(to='shoppingcart.Invoice')),
                ('last_modified_by', models.ForeignKey(related_name='last_modified_by_user', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('currency', models.CharField(default=b'usd', max_length=8)),
                ('status', models.CharField(default=b'cart', max_length=32, choices=[(b'cart', b'cart'), (b'paying', b'paying'), (b'purchased', b'purchased'), (b'refunded', b'refunded'), (b'defunct-cart', b'defunct-cart'), (b'defunct-paying', b'defunct-paying')])),
                ('purchase_time', models.DateTimeField(null=True, blank=True)),
                ('refunded_time', models.DateTimeField(null=True, blank=True)),
                ('bill_to_first', models.CharField(max_length=64, blank=True)),
                ('bill_to_last', models.CharField(max_length=64, blank=True)),
                ('bill_to_street1', models.CharField(max_length=128, blank=True)),
                ('bill_to_street2', models.CharField(max_length=128, blank=True)),
                ('bill_to_city', models.CharField(max_length=64, blank=True)),
                ('bill_to_state', models.CharField(max_length=8, blank=True)),
                ('bill_to_postalcode', models.CharField(max_length=16, blank=True)),
                ('bill_to_country', models.CharField(max_length=64, blank=True)),
                ('bill_to_ccnum', models.CharField(max_length=8, blank=True)),
                ('bill_to_cardtype', models.CharField(max_length=32, blank=True)),
                ('processor_reply_dump', models.TextField(blank=True)),
                ('company_name', models.CharField(max_length=255, null=True, blank=True)),
                ('company_contact_name', models.CharField(max_length=255, null=True, blank=True)),
                ('company_contact_email', models.CharField(max_length=255, null=True, blank=True)),
                ('recipient_name', models.CharField(max_length=255, null=True, blank=True)),
                ('recipient_email', models.CharField(max_length=255, null=True, blank=True)),
                ('customer_reference_number', models.CharField(max_length=63, null=True, blank=True)),
                ('order_type', models.CharField(default=b'personal', max_length=32, choices=[(b'personal', b'personal'), (b'business', b'business')])),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('status', models.CharField(default=b'cart', max_length=32, db_index=True, choices=[(b'cart', b'cart'), (b'paying', b'paying'), (b'purchased', b'purchased'), (b'refunded', b'refunded'), (b'defunct-cart', b'defunct-cart'), (b'defunct-paying', b'defunct-paying')])),
                ('qty', models.IntegerField(default=1)),
                ('unit_cost', models.DecimalField(default=0.0, max_digits=30, decimal_places=2)),
                ('list_price', models.DecimalField(null=True, max_digits=30, decimal_places=2)),
                ('line_desc', models.CharField(default=b'Misc. Item', max_length=1024)),
                ('currency', models.CharField(default=b'usd', max_length=8)),
                ('fulfilled_time', models.DateTimeField(null=True, db_index=True)),
                ('refund_requested_time', models.DateTimeField(null=True, db_index=True)),
                ('service_fee', models.DecimalField(default=0.0, max_digits=30, decimal_places=2)),
                ('report_comments', models.TextField(default=b'')),
            ],
        ),
        migrations.CreateModel(
            name='PaidCourseRegistrationAnnotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', xmodule_django.models.CourseKeyField(unique=True, max_length=128, db_index=True)),
                ('annotation', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='RegistrationCodeRedemption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('redeemed_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('course_enrollment', models.ForeignKey(to='student.CourseEnrollment', null=True)),
                ('order', models.ForeignKey(to='shoppingcart.Order', null=True)),
                ('redeemed_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('registration_code', models.ForeignKey(to='shoppingcart.CourseRegistrationCode')),
            ],
        ),
        migrations.CreateModel(
            name='CertificateItem',
            fields=[
                ('orderitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoppingcart.OrderItem')),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=128, db_index=True)),
                ('mode', models.SlugField()),
                ('course_enrollment', models.ForeignKey(to='student.CourseEnrollment')),
            ],
            bases=('shoppingcart.orderitem',),
        ),
        migrations.CreateModel(
            name='CourseRegCodeItem',
            fields=[
                ('orderitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoppingcart.OrderItem')),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=128, db_index=True)),
                ('mode', models.SlugField(default=b'honor')),
            ],
            bases=('shoppingcart.orderitem',),
        ),
        migrations.CreateModel(
            name='CourseRegistrationCodeInvoiceItem',
            fields=[
                ('invoiceitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoppingcart.InvoiceItem')),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=128, db_index=True)),
            ],
            bases=('shoppingcart.invoiceitem',),
        ),
        migrations.CreateModel(
            name='Donation',
            fields=[
                ('orderitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoppingcart.OrderItem')),
                ('donation_type', models.CharField(default=b'general', max_length=32, choices=[(b'general', b'A general donation'), (b'course', b'A donation to a particular course')])),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
            ],
            bases=('shoppingcart.orderitem',),
        ),
        migrations.CreateModel(
            name='PaidCourseRegistration',
            fields=[
                ('orderitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoppingcart.OrderItem')),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=128, db_index=True)),
                ('mode', models.SlugField(default=b'honor')),
                ('course_enrollment', models.ForeignKey(to='student.CourseEnrollment', null=True)),
            ],
            bases=('shoppingcart.orderitem',),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='order',
            field=models.ForeignKey(to='shoppingcart.Order'),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='invoice',
            field=models.ForeignKey(to='shoppingcart.Invoice'),
        ),
        migrations.AddField(
            model_name='courseregistrationcode',
            name='invoice',
            field=models.ForeignKey(to='shoppingcart.Invoice', null=True),
        ),
        migrations.AddField(
            model_name='courseregistrationcode',
            name='order',
            field=models.ForeignKey(related_name='purchase_order', to='shoppingcart.Order', null=True),
        ),
        migrations.AddField(
            model_name='couponredemption',
            name='order',
            field=models.ForeignKey(to='shoppingcart.Order'),
        ),
        migrations.AddField(
            model_name='couponredemption',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='courseregistrationcode',
            name='invoice_item',
            field=models.ForeignKey(to='shoppingcart.CourseRegistrationCodeInvoiceItem', null=True),
        ),
    ]
