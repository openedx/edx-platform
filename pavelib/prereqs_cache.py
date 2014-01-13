import hashlib
import os
import errno
BLOCKSIZE = 65536

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

try:
    PREREQS_MD5_DIR = os.environ['PREREQ_CACHE_DIR']
except KeyError:
    PREREQS_MD5_DIR = os.path.join(REPO_ROOT, '.prereqs_cache')


def get_files(dir):

    files = []
    for (dirpath, dirnames, filenames) in os.walk(dir):
        for f in filenames:
            files.extend([os.path.join(dirpath, f)])

    return files


def compute_fingerprint(files, dirs):

    hasher = hashlib.sha1()

    # get the SHA1 digest of contents of files
    for file in files:
        with open(file, 'rb') as fd:
            buf = fd.read(BLOCKSIZE)
            while len(buf) > 0:
                hasher.update(buf)
                buf = fd.read(BLOCKSIZE)

    for dir in dirs:
        for (dirpath, dirnames, filenames) in os.walk(dir):
            for f in filenames:
                hasher.update(f)

    return hasher.hexdigest()


# Hash the contents of all the files, and the names of files in the dirs.
def is_changed(cache_file, files, dirs=[]):

    cache_file_path = os.path.join(PREREQS_MD5_DIR, cache_file) + '.sha1'

    hexdigest = compute_fingerprint(files, dirs)

    files_changed = False

    try:
        with open(cache_file_path, 'r') as fd:
            if fd.read() != hexdigest:
                files_changed = True
    except IOError:
        files_changed = True

    if files_changed:
        try:
            os.makedirs(PREREQS_MD5_DIR)
        except OSError as exception:
            if exception.errno != errno.EEXIST:
                raise

        with open(cache_file_path, 'w') as fd:
            fd.write(hexdigest)

    return files_changed
