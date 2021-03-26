from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_admin', '0004_auto_20160412_1506'),
    ]

    operations = [
        migrations.AlterField(
            model_name='apiaccessrequest',
            name='user',
            field=models.OneToOneField(related_name='api_access_request', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
        ),
    ]
