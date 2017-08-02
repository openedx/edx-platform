"Provides management command to ship tracking logs to cloud storage"

from os import listdir, remove, stat
from os.path import isfile, join

from optparse import make_option

from django.core.management.base import BaseCommand

from openedx.core.storage import get_storage


class Command(BaseCommand):
    """
    Django Management command utility to copy local tracking logs to
    a remote storage environment. While this utility was written with Azure
    Blob Storage in mind, since it uses the Django-Storages abstraction layer
    it should be easily modified - if at all - to work with other Django-Storages
    providers such as S3

    To use this command, be sure to run this utility with an identity that has
    read access to the tracking logs.

    Arguments:

        -p <local-tracking-file-directory-path>
           The path where the tracking files can be found
           DEFAULT: /edx/var/log/tracking

        -c <container-name>
           The name of the remote container/bucket to use
           DEFAULT: 'tracking-logs'

        -f <folder-name>
           The name of the folder in the container/bukcet to
           put these files. This can be used to segregate tracking logs
           from multiple Open edX, in the case that it is a shared storage
           repository. The Open edX hostname might be a good choice of folder.
           NOTE: This is a required parameter with no default.

        -s <storage-name>
           The Open edX Django-Storages provider to use
           DEFAULT: 'openedx.core.storage.AzureStorageExtended'

        -o <overwrite-existing>   (True/False)
            A Boolean flag whether to overwrite existing files in the
            targest destination
            DEFAULT: False (don't overwrite)

        -d <delete_local>   (True/False)
            A Boolean flag whether to delete local log files after successful upload
            DEFAULT: False (don't delete)

    To periodically ship off tracking logs, one can trigger an execution of
    this command to some recurring task (like cron). Be sure to configure your
    environments logrotate so that tracking files are rotated on a periodic
    basis, e.g. daily, hourly, etc. After the system managed logrotation, this
    django command can be trigger to upload rotated out files to remote storage.
    """
    option_list = BaseCommand.option_list + (
        make_option('-p', '--path',
                    metavar='PATH',
                    dest='path',
                    default='/edx/var/log/tracking',
                    help='where to find the tracking logs'),
        make_option('-c', '--container',
                    metavar='CONTAINER',
                    dest='container',
                    default='tracking-logs',
                    help='Which container/bucket to use'),
        make_option('-f', '--folder',
                    metavar='FOLDER',
                    dest='folder',
                    default=None,
                    help='Which folder to put the files in'),
        make_option('-s', '--storage',
                    metavar='STORAGE',
                    dest='storage',
                    # default to Azure blob storage
                    default='openedx.core.storage.AzureStorageExtended',
                    help='Which storage class to use'),
        make_option('-o', '--overwrite',
                    metavar='OVERWRITE',
                    dest='overwrite',
                    default=False,
                    help='Overwrite existing files in remote storage'),
        make_option('-d', '--delete_local',
                    metavar='DELETE',
                    dest='delete_local',
                    default=False,
                    help='Delete local files after successful upload')
    )

    def handle(self, *args, **options):
        storage_class = options['storage']
        folder = options['folder']
        container = options['container']
        path = options['path']
        overwrite = options['overwrite']
        delete_local = options['delete_local']

        if not storage_class or not folder or not container or not path:
            print 'You must specify the -c, -f, -p, and -s parameters for this command'

        storage = get_storage(storage_class, container=container)

        files = [f for f in listdir(path) if isfile(join(path, f)) and f.endswith('.gz')]

        for file in files:
            print 'Inspecting {} ....'.format(file)
            local_path = join(path, file)
            try:
                with open(local_path, 'r') as f:
                    dest_fn = '{}/{}'.format(folder, file)
                    exists = storage.exists(dest_fn)
                    # does it already exist? Don't overwrite
                    if not exists or overwrite:
                        # even if we overwrite, don't do so if filesize has not
                        # changed
                        if exists and overwrite:
                            remote_size = storage.size(dest_fn)
                            local_size = stat(local_path).st_size
                            print '{} {}'.format(remote_size, local_size)
                            if long(remote_size) == long(local_size):
                                print '{} does not appear to have changed since last transfer. Skipping'.format(file)
                                continue

                            # remote storage often don't support updates, so we need to
                            # delete/save pair
                            storage.delete(dest_fn)

                        print 'Shipping {} to remote storage...'.format(file)
                        storage.save(dest_fn, f)

                        if delete_local:
                            print 'Deleting {} from disk...'.format(file)
                            remove(local_path)
                    else:
                        print 'File {} already exists in remote storage. Skipping...'.format(file)
            except Exception, ex:
                print 'Exception: {}'.format(str(ex))
