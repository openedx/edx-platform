# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import jsonfield.fields
import opaque_keys.edx.django.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GradedAssignment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('course_key', opaque_keys.edx.django.models.CourseKeyField(db_index=True, max_length=255)),
                ('usage_key', opaque_keys.edx.django.models.UsageKeyField(max_length=255)),
                ('lti_jwt_endpoint', jsonfield.fields.JSONField()),
                ('lti_jwt_sub', models.CharField(max_length=255)),
                ('lti_lineitem', models.CharField(db_index=True, max_length=255)),
                ('lti_lineitem_tag', models.CharField(max_length=255, null=True)),
                ('created_by_tool', models.BooleanField(default=False)),
                ('version_number', models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='LtiTool',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('issuer', models.CharField(help_text="This will usually look something like 'http://example.com'. Value provided by LTI 1.3 Platform", max_length=255, unique=True)),
                ('client_id', models.CharField(help_text='Value provided by LTI 1.3 Platform', max_length=255)),
                ('auth_login_url', models.CharField(help_text="The platform's OIDC login endpoint. Value provided by LTI 1.3 Platform", max_length=1024, validators=[django.core.validators.URLValidator()])),
                ('auth_token_url', models.CharField(help_text="The platform's service authorization endpoint. Value provided by LTI 1.3 Platform", max_length=1024, validators=[django.core.validators.URLValidator()])),
                ('key_set_url', models.CharField(blank=True, help_text="The platform's JWKS endpoint. Value provided by LTI 1.3 Platform", max_length=1024, null=True, validators=[django.core.validators.URLValidator()])),
                ('key_set', jsonfield.fields.JSONField(blank=True, help_text="In case if platform's JWKS endpoint somehow unavailable you may paste JWKS here. Value provided by LTI 1.3 Platform", null=True)),
                ('deployment_ids', jsonfield.fields.JSONField(default=[], help_text='List of Deployment IDs. Example: ["test-id-1", "test-id-2", ...] Each value is provided by LTI 1.3 Platform. ')),
                ('force_create_lineitem', models.BooleanField(default=False, help_text="Forcibly post grades if Platform's assignments grades service is available but lineitem wasn't passed during LTI communication")),
            ],
        ),
        migrations.CreateModel(
            name='LtiToolKey',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Key name', max_length=255, unique=True)),
                ('private_key', models.TextField(help_text="Tool's generated Private key. Keep this value in secret")),
                ('public_key', models.TextField(help_text="Tool's generated Public key. Provide this value to Platforms")),
                ('public_jwk', jsonfield.fields.JSONField(help_text="Tool's generated Public key (from the field above) presented as JWK. Provide this value to Platforms")),
            ],
        ),
        migrations.CreateModel(
            name='LtiUser',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lti_jwt_sub', models.CharField(max_length=255)),
                ('edx_user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='lti1p3_users', to=settings.AUTH_USER_MODEL)),
                ('lti_tool', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lti1p3_tool.LtiTool')),
            ],
        ),
        migrations.AddField(
            model_name='ltitool',
            name='tool_key',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lti1p3_tool.LtiToolKey'),
        ),
        migrations.AddField(
            model_name='gradedassignment',
            name='lti_tool',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='lti1p3_tool.LtiTool'),
        ),
        migrations.AddField(
            model_name='gradedassignment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lti1p3_graded_assignments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterUniqueTogether(
            name='ltiuser',
            unique_together=set([('lti_tool', 'lti_jwt_sub')]),
        ),
        migrations.AlterUniqueTogether(
            name='gradedassignment',
            unique_together=set([('lti_lineitem', 'lti_jwt_sub')]),
        ),
        migrations.AlterIndexTogether(
            name='gradedassignment',
            index_together=set([('lti_jwt_sub', 'lti_lineitem_tag')]),
        ),
    ]
