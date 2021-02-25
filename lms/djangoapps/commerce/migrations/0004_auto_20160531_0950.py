from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commerce', '0003_auto_20160329_0709'),
    ]

    operations = [
        migrations.AddField(
            model_name='commerceconfiguration',
            name='cache_ttl',
            field=models.PositiveIntegerField(default=0, help_text='Specified in seconds. Enable caching by setting this to a value greater than 0.', verbose_name='Cache Time To Live'),
        ),
        migrations.AddField(
            model_name='commerceconfiguration',
            name='receipt_page',
            field=models.CharField(default='/commerce/checkout/receipt/?orderNum=', help_text='Path to order receipt page.', max_length=255),
        ),
    ]
