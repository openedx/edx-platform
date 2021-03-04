from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('credit', '0003_auto_20160511_2227'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='historicalcreditrequest',
            name='course',
        ),
        migrations.RemoveField(
            model_name='historicalcreditrequest',
            name='history_user',
        ),
        migrations.RemoveField(
            model_name='historicalcreditrequest',
            name='provider',
        ),
        migrations.RemoveField(
            model_name='historicalcreditrequirementstatus',
            name='history_user',
        ),
        migrations.RemoveField(
            model_name='historicalcreditrequirementstatus',
            name='requirement',
        ),
        migrations.DeleteModel(
            name='HistoricalCreditRequest',
        ),
        migrations.DeleteModel(
            name='HistoricalCreditRequirementStatus',
        ),
    ]
