from os import listdir, stat
from os.path import isfile, join

from optparse import make_option

from django.core.management.base import BaseCommand

from openedx.core.storage import get_storage


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option('-p', '--path',
            metavar='PATH',
            dest='path',
            default='/edx/var/log/tracking',
            help='where to find the tracking logs',
        ),
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
            help='Overwrite existing files in remote storage')
    )

    def handle(self, *args, **options):
        storage_class = options['storage']
        folder = options['folder']
        container = options['container']
        path = options['path']
        overwrite = options['overwrite']

        if not storage_class or not folder or not container or not path:
            print 'You must specify the -c, -f, -p, and -s parameters for this command'

        storage = get_storage(storage_class, container=container)

        files = [f for f in listdir(path) if isfile(join(path, f))]

        for file in files:
            print 'Inspecting {} ....'.format(file)
            local_path = join(path, file)
            try:
                with open(local_path,'r') as f:
                    dest_fn = '{}/{}'.format(folder, file)
                    exists = storage.exists(dest_fn)
                    # does it already exist? Don't overwrite
                    if not exists or overwrite:
                        # even if we overwrite, don't do so if filesize has not
                        # changed
                        if overwrite:
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
                    else:
                        print 'File {} already exists in remote storage. Skipping...'.format(file)
            except Exception, ex:
                print 'Exception: {}'.format(str(ex))

