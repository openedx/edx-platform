from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('commerce', '123'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commerceconfiguration',
            name='receipt_page',
            field=models.CharField(default='/checkout/receipt/?order_number=', help_text='Path to order receipt page.', max_length=255),
        ),
    ]
