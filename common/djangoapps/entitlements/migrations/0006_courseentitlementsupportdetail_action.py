from django.db import migrations, models


class Migration(migrations.Migration):  # lint-amnesty, pylint: disable=missing-class-docstring

    dependencies = [
        ('entitlements', '0005_courseentitlementsupportdetail'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseentitlementsupportdetail',
            name='action',
            field=models.CharField(default='CREATE', max_length=15, choices=[('REISSUE', 'Re-issue entitlement'), ('CREATE', 'Create new entitlement')]),  # lint-amnesty, pylint: disable=line-too-long
            preserve_default=False,
        ),
    ]
