# -*- coding: utf-8 -*-


from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_admin', '0006_catalog'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalapiaccessrequest',
            name='history_user',
        ),
        migrations.RemoveField(
            model_name='historicalapiaccessrequest',
            name='site',
        ),
        migrations.RemoveField(
            model_name='historicalapiaccessrequest',
            name='user',
        ),
        migrations.DeleteModel(
            name='HistoricalApiAccessRequest',
        ),
    ]
