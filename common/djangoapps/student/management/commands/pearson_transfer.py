import os
from optparse import make_option
from stat import S_ISDIR

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from dogapi import dog_http_api, dog_stats_api
import paramiko
import boto

dog_http_api.api_key = settings.DATADOG_API
dog_stats_api.start(api_key=settings.DATADOG_API, statsd=True)


class Command(BaseCommand):
    help = """
    This command handles the importing and exporting of student records for
    Pearson.  It uses some other Django commands to export and import the
    files and then uploads over SFTP to Pearson and stuffs the entry in an
    S3 bucket for archive purposes.

    Usage: ./manage.py pearson-transfer --mode [import|export|both]
    """

    option_list = BaseCommand.option_list + (
        make_option('--mode',
                    action='store',
                    dest='mode',
                    default='both',
                    choices=('import', 'export', 'both'),
                    help='mode is import, export, or both'),
    )

    def handle(self, **options):

        if not hasattr(settings, 'PEARSON'):
            raise CommandError('No PEARSON entries in auth/env.json.')

        # check settings needed for either import or export:
        for value in ['SFTP_HOSTNAME', 'SFTP_USERNAME', 'SFTP_PASSWORD', 'S3_BUCKET']:
            if value not in settings.PEARSON:
                raise CommandError('No entry in the PEARSON settings'
                                   '(env/auth.json) for {0}'.format(value))

        for value in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']:
            if not hasattr(settings, value):
                raise CommandError('No entry in the AWS settings'
                                   '(env/auth.json) for {0}'.format(value))

        # check additional required settings for import and export:
        if options['mode'] in ('export', 'both'):
            for value in ['LOCAL_EXPORT', 'SFTP_EXPORT']:
                if value not in settings.PEARSON:
                    raise CommandError('No entry in the PEARSON settings'
                                       '(env/auth.json) for {0}'.format(value))
            # make sure that the import directory exists or can be created:
            source_dir = settings.PEARSON['LOCAL_EXPORT']
            if not os.path.isdir(source_dir):
                os.makedirs(source_dir)

        if options['mode'] in ('import', 'both'):
            for value in ['LOCAL_IMPORT', 'SFTP_IMPORT']:
                if value not in settings.PEARSON:
                    raise CommandError('No entry in the PEARSON settings'
                                       '(env/auth.json) for {0}'.format(value))
            # make sure that the import directory exists or can be created:
            dest_dir = settings.PEARSON['LOCAL_IMPORT']
            if not os.path.isdir(dest_dir):
                os.makedirs(dest_dir)


        def sftp(files_from, files_to, mode, deleteAfterCopy=False):
            with dog_stats_api.timer('pearson.{0}'.format(mode), tags='sftp'):
                try:
                    t = paramiko.Transport((settings.PEARSON['SFTP_HOSTNAME'], 22))
                    t.connect(username=settings.PEARSON['SFTP_USERNAME'],
                              password=settings.PEARSON['SFTP_PASSWORD'])
                    sftp = paramiko.SFTPClient.from_transport(t)

                    if mode == 'export':
                        try:
                            sftp.chdir(files_to)
                        except IOError:
                            raise CommandError('SFTP destination path does not exist: {}'.format(files_to))
                        for filename in os.listdir(files_from):
                            sftp.put(files_from + '/' + filename, filename)
                            if deleteAfterCopy:
                                os.remove(os.path.join(files_from, filename))
                    else:
                        try:
                            sftp.chdir(files_from)
                        except IOError:
                            raise CommandError('SFTP source path does not exist: {}'.format(files_from))
                        for filename in sftp.listdir('.'):
                            # skip subdirectories
                            if not S_ISDIR(sftp.stat(filename).st_mode):
                                sftp.get(filename, files_to + '/' + filename)
                                # delete files from sftp server once they are successfully pulled off:
                                if deleteAfterCopy:
                                    sftp.remove(filename)
                except:
                    dog_http_api.event('pearson {0}'.format(mode),
                                       'sftp uploading failed',
                                       alert_type='error')
                    raise
                finally:
                    sftp.close()
                    t.close()

        def s3(files_from, bucket, mode, deleteAfterCopy=False):
            with dog_stats_api.timer('pearson.{0}'.format(mode), tags='s3'):
                try:
                    for filename in os.listdir(files_from):
                        source_file = os.path.join(files_from, filename)
                        # use mode as name of directory into which to write files
                        dest_file = os.path.join(mode, filename)
                        upload_file_to_s3(bucket, source_file, dest_file)
                        if deleteAfterCopy:
                            os.remove(files_from + '/' + filename)
                except:
                    dog_http_api.event('pearson {0}'.format(mode),
                                       's3 archiving failed')
                    raise

        def upload_file_to_s3(bucket, source_file, dest_file):
            """
            Upload file to S3
            """
            s3 = boto.connect_s3(settings.AWS_ACCESS_KEY_ID,
                                 settings.AWS_SECRET_ACCESS_KEY)
            from boto.s3.key import Key
            b = s3.get_bucket(bucket)
            k = Key(b)
            k.key = "{filename}".format(filename=dest_file)
            k.set_contents_from_filename(source_file)

        def export_pearson():
            options = {'dest-from-settings': True}
            call_command('pearson_export_cdd', **options)
            call_command('pearson_export_ead', **options)
            mode = 'export'
            sftp(settings.PEARSON['LOCAL_EXPORT'], settings.PEARSON['SFTP_EXPORT'], mode, deleteAfterCopy=False)
            s3(settings.PEARSON['LOCAL_EXPORT'], settings.PEARSON['S3_BUCKET'], mode, deleteAfterCopy=True)

        def import_pearson():
            mode = 'import'
            try:
                sftp(settings.PEARSON['SFTP_IMPORT'], settings.PEARSON['LOCAL_IMPORT'], mode, deleteAfterCopy=True)
                s3(settings.PEARSON['LOCAL_IMPORT'], settings.PEARSON['S3_BUCKET'], mode, deleteAfterCopy=False)
            except Exception as e:
                dog_http_api.event('Pearson Import failure', str(e))
                raise e
            else:
                for filename in os.listdir(settings.PEARSON['LOCAL_IMPORT']):
                    filepath = os.path.join(settings.PEARSON['LOCAL_IMPORT'], filename)
                    call_command('pearson_import_conf_zip', filepath)
                    os.remove(filepath)

        # actually do the work!
        if options['mode'] in ('export', 'both'):
            export_pearson()
        if options['mode'] in ('import', 'both'):
            import_pearson()
