# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entitlements', '0005_courseentitlementsupportdetail'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseentitlementsupportdetail',
            name='action',
            field=models.CharField(default='CREATE', max_length=15, choices=[(u'REISSUE', u'Re-issue entitlement'), (u'CREATE', u'Create new entitlement')]),
            preserve_default=False,
        ),
    ]
