# -*- coding: utf-8 -*-


from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('entitlements', '0007_change_expiration_period_default'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseentitlementpolicy',
            name='mode',
            field=models.CharField(max_length=32, null=True, choices=[(None, u'---------'), (u'verified', u'verified'), (u'professional', u'professional')]),
        ),
        migrations.AlterField(
            model_name='courseentitlementpolicy',
            name='site',
            field=models.ForeignKey(to='sites.Site', null=True, on_delete=models.CASCADE),
        ),
    ]
