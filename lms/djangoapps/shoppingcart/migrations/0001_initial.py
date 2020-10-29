# -*- coding: utf-8 -*-


import django.db.models.deletion
import django.utils.timezone
import model_utils.fields
from django.conf import settings
from django.db import migrations, models
from opaque_keys.edx.django.models import CourseKeyField


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
                ('course_id', CourseKeyField(max_length=255)),
                ('percentage_discount', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('is_active', models.BooleanField(default=True)),
                ('expiration_date', models.DateTimeField(null=True, blank=True)),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='CouponRedemption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('coupon', models.ForeignKey(to='shoppingcart.Coupon', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='CourseRegCodeItemAnnotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', CourseKeyField(unique=True, max_length=128, db_index=True)),
                ('annotation', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CourseRegistrationCode',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(unique=True, max_length=32, db_index=True)),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('mode_slug', models.CharField(max_length=100, null=True)),
                ('is_valid', models.BooleanField(default=True)),
                ('created_by', models.ForeignKey(related_name='created_by_user', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
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
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
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
                ('invoice', models.ForeignKey(to='shoppingcart.Invoice', on_delete=models.CASCADE)),
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
                ('currency', models.CharField(default=u'usd', help_text='Lower-case ISO currency codes', max_length=8)),
            ],
        ),
        migrations.CreateModel(
            name='InvoiceTransaction',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('amount', models.DecimalField(default=0.0, help_text='The amount of the transaction.  Use positive amounts for payments and negative amounts for refunds.', max_digits=30, decimal_places=2)),
                ('currency', models.CharField(default=u'usd', help_text='Lower-case ISO currency codes', max_length=8)),
                ('comments', models.TextField(help_text='Optional: provide additional information for this transaction', null=True, blank=True)),
                ('status', models.CharField(default=u'started', help_text="The status of the payment or refund. 'started' means that payment is expected, but money has not yet been transferred. 'completed' means that the payment or refund was received. 'cancelled' means that payment or refund was expected, but was cancelled before money was transferred. ", max_length=32, choices=[(u'started', u'started'), (u'completed', u'completed'), (u'cancelled', u'cancelled')])),
                ('created_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('invoice', models.ForeignKey(to='shoppingcart.Invoice', on_delete=models.CASCADE)),
                ('last_modified_by', models.ForeignKey(related_name='last_modified_by_user', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('currency', models.CharField(default=u'usd', max_length=8)),
                ('status', models.CharField(default=u'cart', max_length=32, choices=[(u'cart', u'cart'), (u'paying', u'paying'), (u'purchased', u'purchased'), (u'refunded', u'refunded'), (u'defunct-cart', u'defunct-cart'), (u'defunct-paying', u'defunct-paying')])),
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
                ('order_type', models.CharField(default=u'personal', max_length=32, choices=[(u'personal', u'personal'), (u'business', u'business')])),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='OrderItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, verbose_name='created', editable=False)),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, verbose_name='modified', editable=False)),
                ('status', models.CharField(default=u'cart', max_length=32, db_index=True, choices=[(u'cart', u'cart'), (u'paying', u'paying'), (u'purchased', u'purchased'), (u'refunded', u'refunded'), (u'defunct-cart', u'defunct-cart'), (u'defunct-paying', u'defunct-paying')])),
                ('qty', models.IntegerField(default=1)),
                ('unit_cost', models.DecimalField(default=0.0, max_digits=30, decimal_places=2)),
                ('list_price', models.DecimalField(null=True, max_digits=30, decimal_places=2)),
                ('line_desc', models.CharField(default=u'Misc. Item', max_length=1024)),
                ('currency', models.CharField(default=u'usd', max_length=8)),
                ('fulfilled_time', models.DateTimeField(null=True, db_index=True)),
                ('refund_requested_time', models.DateTimeField(null=True, db_index=True)),
                ('service_fee', models.DecimalField(default=0.0, max_digits=30, decimal_places=2)),
                ('report_comments', models.TextField(default=u'')),
            ],
        ),
        migrations.CreateModel(
            name='PaidCourseRegistrationAnnotation',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', CourseKeyField(unique=True, max_length=128, db_index=True)),
                ('annotation', models.TextField(null=True)),
            ],
        ),
        migrations.CreateModel(
            name='RegistrationCodeRedemption',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('redeemed_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('course_enrollment', models.ForeignKey(to='student.CourseEnrollment', null=True, on_delete=models.CASCADE)),
                ('order', models.ForeignKey(to='shoppingcart.Order', null=True, on_delete=models.CASCADE)),
                ('redeemed_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
                ('registration_code', models.ForeignKey(to='shoppingcart.CourseRegistrationCode', on_delete=models.CASCADE)),
            ],
        ),
        migrations.CreateModel(
            name='CertificateItem',
            fields=[
                ('orderitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoppingcart.OrderItem', on_delete=models.CASCADE)),
                ('course_id', CourseKeyField(max_length=128, db_index=True)),
                ('mode', models.SlugField()),
                ('course_enrollment', models.ForeignKey(to='student.CourseEnrollment', on_delete=models.CASCADE)),
            ],
            bases=('shoppingcart.orderitem',),
        ),
        migrations.CreateModel(
            name='CourseRegCodeItem',
            fields=[
                ('orderitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoppingcart.OrderItem', on_delete=models.CASCADE)),
                ('course_id', CourseKeyField(max_length=128, db_index=True)),
                ('mode', models.SlugField(default=b'honor')),
            ],
            bases=('shoppingcart.orderitem',),
        ),
        migrations.CreateModel(
            name='CourseRegistrationCodeInvoiceItem',
            fields=[
                ('invoiceitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoppingcart.InvoiceItem', on_delete=models.CASCADE)),
                ('course_id', CourseKeyField(max_length=128, db_index=True)),
            ],
            bases=('shoppingcart.invoiceitem',),
        ),
        migrations.CreateModel(
            name='Donation',
            fields=[
                ('orderitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoppingcart.OrderItem', on_delete=models.CASCADE)),
                ('donation_type', models.CharField(default=u'general', max_length=32, choices=[(u'general', u'A general donation'), (u'course', u'A donation to a particular course')])),
                ('course_id', CourseKeyField(max_length=255, db_index=True)),
            ],
            bases=('shoppingcart.orderitem',),
        ),
        migrations.CreateModel(
            name='PaidCourseRegistration',
            fields=[
                ('orderitem_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='shoppingcart.OrderItem', on_delete=models.CASCADE)),
                ('course_id', CourseKeyField(max_length=128, db_index=True)),
                ('mode', models.SlugField(default=b'honor')),
                ('course_enrollment', models.ForeignKey(to='student.CourseEnrollment', null=True, on_delete=models.CASCADE)),
            ],
            bases=('shoppingcart.orderitem',),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='order',
            field=models.ForeignKey(to='shoppingcart.Order', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='orderitem',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='invoiceitem',
            name='invoice',
            field=models.ForeignKey(to='shoppingcart.Invoice', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='courseregistrationcode',
            name='invoice',
            field=models.ForeignKey(to='shoppingcart.Invoice', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='courseregistrationcode',
            name='order',
            field=models.ForeignKey(related_name='purchase_order', to='shoppingcart.Order', null=True, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='couponredemption',
            name='order',
            field=models.ForeignKey(to='shoppingcart.Order', on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='couponredemption',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
        migrations.AddField(
            model_name='courseregistrationcode',
            name='invoice_item',
            field=models.ForeignKey(to='shoppingcart.CourseRegistrationCodeInvoiceItem', null=True, on_delete=models.CASCADE),
        ),
    ]
