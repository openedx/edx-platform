# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commerce', '0005_commerceconfiguration_enable_automatic_refund_approval'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commerceconfiguration',
            name='receipt_page',
            field=models.CharField(default=u'/checkout/receipt/?order_number=', help_text='Path to order receipt page.', max_length=255),
        ),
    ]
