from optparse import make_option

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
import re
from dogapi import dog_http_api, dog_stats_api
import paramiko
import boto

dog_http_api.api_key = settings.DATADOG_API


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--mode',
                    action='store',
                    dest='mode',
                    default='both',
                    help='mode is import, export, or both'),
    )

    def handle(self, **options):

        if not settings.PEARSON:
            raise CommandError('No PEARSON entries in auth/env.json.')

        def import_pearson():
            sftp(settings.PEARSON[SFTP_IMPORT], settings.PEARSON[LOCAL_IMPORT])
            s3(settings.PEARSON[LOCAL_IMPORT], settings.PEARSON[BUCKET])
            call_command('pearson_import', 'dest_from_settings=True')

        def export_pearson():
            call_command('pearson_export_ccd', 'dest_from_settings=True')
            call_command('pearson_export_ead', 'dest_from_settings=True')
            sftp(settings.PEARSON[LOCAL_EXPORT], settings.PEARSON[SFTP_EXPORT])
            s3(settings.PEARSON[LOCAL_EXPORT], settings.PEARSON[BUCKET])

        if options['mode'] == 'both':
            export_pearson()
            import_pearson()
        elif options['mode'] == 'export':
            export_pearson()
        elif options['mode'] == 'import':
            import_pearson()
        else:
            print("ERROR:  Mode must be export or import.")


        def sftp(files_from, files_to):
            with dog_stats_api.timer('pearson.{0}'.format(mode), tags='sftp'):
                try:
                    t = paramiko.Transport((hostname, 22))
                    t.connect(username=settings.PEARSON[SFTP_USERNAME],
                              password=settings.PEARSON[SFTP_PASSWORD])
                    sftp = paramiko.SFTPClient.from_transport(t)
                    if os.path.isdir(files_from):
                        for filename in os.listdir(files_from):
                            sftp.put(files_from+'/'+filename,
                                     files_to+'/'+filename)
                    else:
                        for filename in sftp.listdir(files_from):
                            sftp.get(files_from+'/'+filename,
                                     files_to+'/'+filename)
                except:
                    dog_http_api.event('pearson {0}'.format(mode),
                                       'sftp uploading failed', alert_type='error')
                    raise

        def s3(files_from, bucket):
            with dog_stats_api.timer('pearson.{0}'.format(mode), tags='s3'):
                try:
                    for filename in os.listdir(files):
                        upload_file_to_s3(bucket, files_from+'/'+filename)
                except:
                    dog_http_api.event('pearson {0}'.format(mode), 's3 archiving failed')
                    raise


        def upload_file_to_s3(bucket, filename):
            """
            Upload file to S3
            """
            s3 = boto.connect_s3(settings.AWS_ACCESS_KEY_ID,
                    settings.AWS_SECRET_ACCESS_KEY)
            from boto.s3.key import Key
            b = s3.get_bucket(bucket)
            k = Key(b)
            k.key = "{filename}".format(filename=filename)
            k.set_contents_from_filename(filename)
