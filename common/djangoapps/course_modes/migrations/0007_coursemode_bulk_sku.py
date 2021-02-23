from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('course_modes', '0006_auto_20160208_1407'),
    ]

    operations = [
        migrations.AddField(
            model_name='coursemode',
            name='bulk_sku',
            field=models.CharField(default=None, max_length=255, blank=True, help_text='This is the bulk SKU (stock keeping unit) of this mode in the external ecommerce service.', null=True, verbose_name='Bulk SKU'),
        ),
    ]
