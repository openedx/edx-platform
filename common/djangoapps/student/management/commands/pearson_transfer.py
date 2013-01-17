from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from dogapi import dog_http_api, dog_stats_api
import paramiko
import boto
import os

dog_http_api.api_key = settings.DATADOG_API


class Command(BaseCommand):
    help = """
    This command handles the importing and exporting of student records for
    Pearson.  It uses some other Django commands to export and import the
    files and then uploads over SFTP to pearson and stuffs the entry in an
    S3 bucket for archive purposes.

    Usage: django-admin.py pearson-transfer --mode [import|export|both]
    """

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

        for value in ['LOCAL_IMPORT', 'SFTP_IMPORT', 'BUCKET', 'LOCAL_EXPORT',
                      'SFTP_EXPORT']:
            if value not in settings.PEARSON:
                raise CommandError('No entry in the PEARSON settings'
                                   '(env/auth.json) for {0}'.format(value))

        def import_pearson():
            sftp(settings.PEARSON['SFTP_IMPORT'],
                 settings.PEARSON['LOCAL_IMPORT'], options['mode'])
            s3(settings.PEARSON['LOCAL_IMPORT'],
               settings.PEARSON['BUCKET'], options['mode'])
            call_command('pearson_import', 'dest_from_settings')

        def export_pearson():
            call_command('pearson_export_cdd', 'dest_from_settings')
            call_command('pearson_export_ead', 'dest_from_settings')
            sftp(settings.PEARSON['LOCAL_EXPORT'],
                 settings.PEARSON['SFTP_EXPORT'], options['mode'])
            s3(settings.PEARSON['LOCAL_EXPORT'],
               settings.PEARSON['BUCKET'], options['mode'])

        if options['mode'] == 'export':
            export_pearson()
        elif options['mode'] == 'import':
            import_pearson()
        else:
            export_pearson()
            import_pearson()

        def sftp(files_from, files_to, mode):
            with dog_stats_api.timer('pearson.{0}'.format(mode), tags='sftp'):
                try:
                    t = paramiko.Transport((settings.PEARSON['SFTP_HOSTNAME'], 22))
                    t.connect(username=settings.PEARSON['SFTP_USERNAME'],
                              password=settings.PEARSON['SFTP_PASSWORD'])
                    sftp = paramiko.SFTPClient.from_transport(t)
                    if os.path.isdir(files_from):
                        for filename in os.listdir(files_from):
                            sftp.put(files_from + '/' + filename,
                                     files_to + '/' + filename)
                    else:
                        for filename in sftp.listdir(files_from):
                            sftp.get(files_from + '/' + filename,
                                     files_to + '/' + filename)
                    t.close()
                except:
                    dog_http_api.event('pearson {0}'.format(mode),
                                       'sftp uploading failed',
                                       alert_type='error')
                    raise

        def s3(files_from, bucket, mode):
            with dog_stats_api.timer('pearson.{0}'.format(mode), tags='s3'):
                try:
                    for filename in os.listdir(files_from):
                        upload_file_to_s3(bucket, files_from + '/' + filename)
                except:
                    dog_http_api.event('pearson {0}'.format(mode),
                                       's3 archiving failed')
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
