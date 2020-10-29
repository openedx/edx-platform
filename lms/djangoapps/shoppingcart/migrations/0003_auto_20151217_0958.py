# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shoppingcart', '0002_auto_20151208_1034'),
    ]

    operations = [
        migrations.AlterField(
            model_name='courseregcodeitem',
            name='mode',
            field=models.SlugField(default=u'honor'),
        ),
        migrations.AlterField(
            model_name='paidcourseregistration',
            name='mode',
            field=models.SlugField(default=u'honor'),
        ),
    ]
