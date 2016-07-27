# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import django_countries.fields
import django.db.models.deletion
from django.conf import settings
import xmodule_django.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AnonymousUserId',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('anonymous_user_id', models.CharField(unique=True, max_length=32)),
                ('course_id', xmodule_django.models.CourseKeyField(db_index=True, max_length=255, blank=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CourseAccessRole',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('org', models.CharField(db_index=True, max_length=64, blank=True)),
                ('course_id', xmodule_django.models.CourseKeyField(db_index=True, max_length=255, blank=True)),
                ('role', models.CharField(max_length=64, db_index=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='CourseEnrollment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('created', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('mode', models.CharField(default=b'honor', max_length=100)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('user', 'course_id'),
            },
        ),
        migrations.CreateModel(
            name='CourseEnrollmentAllowed',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('email', models.CharField(max_length=255, db_index=True)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('auto_enroll', models.BooleanField(default=0)),
                ('created', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='CourseEnrollmentAttribute',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('namespace', models.CharField(help_text='Namespace of enrollment attribute', max_length=255)),
                ('name', models.CharField(help_text='Name of the enrollment attribute', max_length=255)),
                ('value', models.CharField(help_text='Value of the enrollment attribute', max_length=255)),
                ('enrollment', models.ForeignKey(related_name='attributes', to='student.CourseEnrollment')),
            ],
        ),
        migrations.CreateModel(
            name='DashboardConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('recent_enrollment_time_delta', models.PositiveIntegerField(default=0, help_text=b"The number of seconds in which a new enrollment is considered 'recent'. Used to display notifications.")),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'ordering': ('-change_date',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='EntranceExamConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('course_id', xmodule_django.models.CourseKeyField(max_length=255, db_index=True)),
                ('created', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
                ('updated', models.DateTimeField(auto_now=True, db_index=True)),
                ('skip_entrance_exam', models.BooleanField(default=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='LanguageProficiency',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(help_text='The ISO 639-1 language code for this language.', max_length=16, choices=[['aa', 'Afar'], ['ab', 'Abkhazian'], ['af', 'Afrikaans'], ['ak', 'Akan'], ['sq', 'Albanian'], ['am', 'Amharic'], ['ar', 'Arabic'], ['an', 'Aragonese'], ['hy', 'Armenian'], ['as', 'Assamese'], ['av', 'Avaric'], ['ae', 'Avestan'], ['ay', 'Aymara'], ['az', 'Azerbaijani'], ['ba', 'Bashkir'], ['bm', 'Bambara'], ['eu', 'Basque'], ['be', 'Belarusian'], ['bn', 'Bengali'], ['bh', 'Bihari languages'], ['bi', 'Bislama'], ['bs', 'Bosnian'], ['br', 'Breton'], ['bg', 'Bulgarian'], ['my', 'Burmese'], ['ca', 'Catalan'], ['ch', 'Chamorro'], ['ce', 'Chechen'], ['zh', 'Chinese'], ['zh_HANS', 'Simplified Chinese'], ['zh_HANT', 'Traditional Chinese'], ['cu', 'Church Slavic'], ['cv', 'Chuvash'], ['kw', 'Cornish'], ['co', 'Corsican'], ['cr', 'Cree'], ['cs', 'Czech'], ['da', 'Danish'], ['dv', 'Divehi'], ['nl', 'Dutch'], ['dz', 'Dzongkha'], ['en', 'English'], ['eo', 'Esperanto'], ['et', 'Estonian'], ['ee', 'Ewe'], ['fo', 'Faroese'], ['fj', 'Fijian'], ['fi', 'Finnish'], ['fr', 'French'], ['fy', 'Western Frisian'], ['ff', 'Fulah'], ['ka', 'Georgian'], ['de', 'German'], ['gd', 'Gaelic'], ['ga', 'Irish'], ['gl', 'Galician'], ['gv', 'Manx'], ['el', 'Greek'], ['gn', 'Guarani'], ['gu', 'Gujarati'], ['ht', 'Haitian'], ['ha', 'Hausa'], ['he', 'Hebrew'], ['hz', 'Herero'], ['hi', 'Hindi'], ['ho', 'Hiri Motu'], ['hr', 'Croatian'], ['hu', 'Hungarian'], ['ig', 'Igbo'], ['is', 'Icelandic'], ['io', 'Ido'], ['ii', 'Sichuan Yi'], ['iu', 'Inuktitut'], ['ie', 'Interlingue'], ['ia', 'Interlingua'], ['id', 'Indonesian'], ['ik', 'Inupiaq'], ['it', 'Italian'], ['jv', 'Javanese'], ['ja', 'Japanese'], ['kl', 'Kalaallisut'], ['kn', 'Kannada'], ['ks', 'Kashmiri'], ['kr', 'Kanuri'], ['kk', 'Kazakh'], ['km', 'Central Khmer'], ['ki', 'Kikuyu'], ['rw', 'Kinyarwanda'], ['ky', 'Kirghiz'], ['kv', 'Komi'], ['kg', 'Kongo'], ['ko', 'Korean'], ['kj', 'Kuanyama'], ['ku', 'Kurdish'], ['lo', 'Lao'], ['la', 'Latin'], ['lv', 'Latvian'], ['li', 'Limburgan'], ['ln', 'Lingala'], ['lt', 'Lithuanian'], ['lb', 'Luxembourgish'], ['lu', 'Luba-Katanga'], ['lg', 'Ganda'], ['mk', 'Macedonian'], ['mh', 'Marshallese'], ['ml', 'Malayalam'], ['mi', 'Maori'], ['mr', 'Marathi'], ['ms', 'Malay'], ['mg', 'Malagasy'], ['mt', 'Maltese'], ['mn', 'Mongolian'], ['na', 'Nauru'], ['nv', 'Navajo'], ['nr', 'Ndebele, South'], ['nd', 'Ndebele, North'], ['ng', 'Ndonga'], ['ne', 'Nepali'], ['nn', 'Norwegian Nynorsk'], ['nb', 'Bokm\xe5l, Norwegian'], ['no', 'Norwegian'], ['ny', 'Chichewa'], ['oc', 'Occitan'], ['oj', 'Ojibwa'], ['or', 'Oriya'], ['om', 'Oromo'], ['os', 'Ossetian'], ['pa', 'Panjabi'], ['fa', 'Persian'], ['pi', 'Pali'], ['pl', 'Polish'], ['pt', 'Portuguese'], ['ps', 'Pushto'], ['qu', 'Quechua'], ['rm', 'Romansh'], ['ro', 'Romanian'], ['rn', 'Rundi'], ['ru', 'Russian'], ['sg', 'Sango'], ['sa', 'Sanskrit'], ['si', 'Sinhala'], ['sk', 'Slovak'], ['sl', 'Slovenian'], ['se', 'Northern Sami'], ['sm', 'Samoan'], ['sn', 'Shona'], ['sd', 'Sindhi'], ['so', 'Somali'], ['st', 'Sotho, Southern'], ['es', 'Spanish'], ['sc', 'Sardinian'], ['sr', 'Serbian'], ['ss', 'Swati'], ['su', 'Sundanese'], ['sw', 'Swahili'], ['sv', 'Swedish'], ['ty', 'Tahitian'], ['ta', 'Tamil'], ['tt', 'Tatar'], ['te', 'Telugu'], ['tg', 'Tajik'], ['tl', 'Tagalog'], ['th', 'Thai'], ['bo', 'Tibetan'], ['ti', 'Tigrinya'], ['to', 'Tonga (Tonga Islands)'], ['tn', 'Tswana'], ['ts', 'Tsonga'], ['tk', 'Turkmen'], ['tr', 'Turkish'], ['tw', 'Twi'], ['ug', 'Uighur'], ['uk', 'Ukrainian'], ['ur', 'Urdu'], ['uz', 'Uzbek'], ['ve', 'Venda'], ['vi', 'Vietnamese'], ['vo', 'Volap\xfck'], ['cy', 'Welsh'], ['wa', 'Walloon'], ['wo', 'Wolof'], ['xh', 'Xhosa'], ['yi', 'Yiddish'], ['yo', 'Yoruba'], ['za', 'Zhuang'], ['zu', 'Zulu']])),
            ],
        ),
        migrations.CreateModel(
            name='LinkedInAddToProfileConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('change_date', models.DateTimeField(auto_now_add=True, verbose_name='Change date')),
                ('enabled', models.BooleanField(default=False, verbose_name='Enabled')),
                ('company_identifier', models.TextField(help_text='The company identifier for the LinkedIn Add-to-Profile button e.g 0_0dPSPyS070e0HsE9HNz_13_d11_')),
                ('dashboard_tracking_code', models.TextField(default=b'', blank=True)),
                ('trk_partner_name', models.CharField(default=b'', help_text="Short identifier for the LinkedIn partner used in the tracking code.  (Example: 'edx')  If no value is provided, tracking codes will not be sent to LinkedIn.", max_length=10, blank=True)),
                ('changed_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, editable=False, to=settings.AUTH_USER_MODEL, null=True, verbose_name='Changed by')),
            ],
            options={
                'ordering': ('-change_date',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='LoginFailures',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('failure_count', models.IntegerField(default=0)),
                ('lockout_until', models.DateTimeField(null=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ManualEnrollmentAudit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('enrolled_email', models.CharField(max_length=255, db_index=True)),
                ('time_stamp', models.DateTimeField(auto_now_add=True, null=True)),
                ('state_transition', models.CharField(max_length=255, choices=[(b'from unenrolled to allowed to enroll', b'from unenrolled to allowed to enroll'), (b'from allowed to enroll to enrolled', b'from allowed to enroll to enrolled'), (b'from enrolled to enrolled', b'from enrolled to enrolled'), (b'from enrolled to unenrolled', b'from enrolled to unenrolled'), (b'from unenrolled to enrolled', b'from unenrolled to enrolled'), (b'from allowed to enroll to enrolled', b'from allowed to enroll to enrolled'), (b'from unenrolled to unenrolled', b'from unenrolled to unenrolled'), (b'N/A', b'N/A')])),
                ('reason', models.TextField(null=True)),
                ('enrolled_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True)),
                ('enrollment', models.ForeignKey(to='student.CourseEnrollment', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PasswordHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128)),
                ('time_set', models.DateTimeField(default=django.utils.timezone.now)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PendingEmailChange',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('new_email', models.CharField(db_index=True, max_length=255, blank=True)),
                ('activation_key', models.CharField(unique=True, max_length=32, verbose_name=b'activation key', db_index=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PendingNameChange',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('new_name', models.CharField(max_length=255, blank=True)),
                ('rationale', models.CharField(max_length=1024, blank=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Registration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('activation_key', models.CharField(unique=True, max_length=32, verbose_name=b'activation key', db_index=True)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'auth_registration',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(db_index=True, max_length=255, blank=True)),
                ('meta', models.TextField(blank=True)),
                ('courseware', models.CharField(default=b'course.xml', max_length=255, blank=True)),
                ('language', models.CharField(db_index=True, max_length=255, blank=True)),
                ('location', models.CharField(db_index=True, max_length=255, blank=True)),
                ('year_of_birth', models.IntegerField(db_index=True, null=True, blank=True)),
                ('gender', models.CharField(blank=True, max_length=6, null=True, db_index=True, choices=[(b'm', b'Male'), (b'f', b'Female'), (b'o', b'Other/Prefer Not to Say')])),
                ('level_of_education', models.CharField(blank=True, max_length=6, null=True, db_index=True, choices=[(b'p', b'Doctorate'), (b'm', b"Master's or professional degree"), (b'b', b"Bachelor's degree"), (b'a', b'Associate degree'), (b'hs', b'Secondary/high school'), (b'jhs', b'Junior secondary/junior high/middle school'), (b'el', b'Elementary/primary school'), (b'none', b'No Formal Education'), (b'other', b'Other Education')])),
                ('mailing_address', models.TextField(null=True, blank=True)),
                ('city', models.TextField(null=True, blank=True)),
                ('country', django_countries.fields.CountryField(blank=True, max_length=2, null=True)),
                ('goals', models.TextField(null=True, blank=True)),
                ('allow_certificate', models.BooleanField(default=1)),
                ('bio', models.CharField(max_length=3000, null=True, blank=True)),
                ('profile_image_uploaded_at', models.DateTimeField(null=True)),
                ('title', models.CharField(max_length=255, null=True, blank=True)),
                ('avatar_url', models.CharField(max_length=255, null=True, blank=True)),
                ('user', models.OneToOneField(related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'auth_userprofile',
            },
        ),
        migrations.CreateModel(
            name='UserSignupSource',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('site', models.CharField(max_length=255, db_index=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserStanding',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('account_status', models.CharField(blank=True, max_length=31, choices=[(b'disabled', 'Account Disabled'), (b'enabled', 'Account Enabled')])),
                ('standing_last_changed_at', models.DateTimeField(auto_now=True)),
                ('changed_by', models.ForeignKey(to=settings.AUTH_USER_MODEL, blank=True)),
                ('user', models.OneToOneField(related_name='standing', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserTestGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=32, db_index=True)),
                ('description', models.TextField(blank=True)),
                ('users', models.ManyToManyField(to=settings.AUTH_USER_MODEL, db_index=True)),
            ],
        ),
        migrations.AddField(
            model_name='languageproficiency',
            name='user_profile',
            field=models.ForeignKey(related_name='language_proficiencies', to='student.UserProfile'),
        ),
        migrations.AlterUniqueTogether(
            name='courseenrollmentallowed',
            unique_together=set([('email', 'course_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='languageproficiency',
            unique_together=set([('code', 'user_profile')]),
        ),
        migrations.AlterUniqueTogether(
            name='entranceexamconfiguration',
            unique_together=set([('user', 'course_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='courseenrollment',
            unique_together=set([('user', 'course_id')]),
        ),
        migrations.AlterUniqueTogether(
            name='courseaccessrole',
            unique_together=set([('user', 'org', 'course_id', 'role')]),
        ),
    ]
