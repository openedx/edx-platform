#!/usr/bin/env python
"""
This script is intended to be used to store the ~/.pip/download-cache
directory in S3. The primary use case, as of this writing, is to help
speed up Jenkins build times for edx-platform tests.

Before running pip-accel install (or pip install) on a Jenkins worker,
this directory will be downloaded from S3.

For usage:  `python pip_cache_store.py -h`.
"""
import argparse
from boto.s3.connection import S3Connection
from boto.exception import S3ResponseError
import os
from path import path
import sys
import tarfile


class S3TarStore():
    """
    Static methods for storing directories in S3 in tar.gz form.
    """

    def __init__(self, *args, **kwargs):
        self.dirpath = kwargs['dirpath']
        self.tarpath = kwargs['tarpath']
        self.bucket_name = kwargs['bucket_name']
        self.keyname = path(kwargs['bucket_folder']) / self.tarpath.basename()

    @staticmethod
    def bucket(bucket_name):
        """
        Returns bucket matching name. If there exists no such bucket
        or there is an exception raised, then `None` is returned.
        """
        try:
            conn = S3Connection()
            bucket = conn.get_bucket(bucket_name)
        except S3ResponseError:
            print ( 
                "Please check that the bucket {} exists and that you have "
                "the proper credentials to access it.".format(bucket_name)
            )
            return None
        except Exception as e:
            print (
                "There was an error while connecting to S3. "
                "Please check error log for more details."
            )
            sys.stderr.write(e.message)
            return None

        if not bucket:
            print "No such bucket {}.".format(self.bucket_name)

        return bucket


    @staticmethod
    def download_dir(bucket, tarpath, dirpath, keyname):
        """
        Downloads a file matching `keyname` from `bucket`
        to `tarpath`. It then extracts the tar.gz file into `dirpath`.
        If no matching `keyname` is found, it does nothing.

        Note that any exceptions that occur while downloading or unpacking
        will be logged, but not raised.
        """
        key = bucket.lookup(keyname)
        if key:
            try:
                print "Downloading contents of {} from S3.".format(keyname)
                key.get_contents_to_filename(tarpath)

                with tarfile.open(tarpath, mode="r:gz") as tar:
                    print "Unpacking {} to {}".format(tarpath, dirpath)
                    tar.extractall(path=dirpath.parent)
            except Exception as e:
                print ("Ignored Exception:\n {}".format(e.message))
        else:
            print (
                "Couldn't find anything matching {} in S3 bucket. "
                "Doing Nothing.".format(keyname)
            )

    @staticmethod
    def upload_dir(bucket, tarpath, dirpath, keyname):
        """
        Packs the contents of `dirpath` into a tar.gz file named
        `tarpath.basename()`. It then uploads the tar.gz file to `bucket`
        as `keyname`. If `dirpath` is not a directory, it does nothing.

        Note that any exceptions that occur while compressing or uploading
        will be logged, but not raised.
        # """
        if dirpath.isdir():
            try:
                with tarfile.open(tarpath, "w:gz") as tar:
                    print "Packing up {} to {}".format(dirpath, tarpath)
                    tar.add(dirpath, arcname='/')

                print "Uploading {} to S3 bucket.".format(keyname)
                existing_key = bucket.lookup(keyname)
                key = existing_key if existing_key else bucket.new_key(keyname)
                key.set_contents_from_filename(tarpath)
            except Exception as e:
                print ("Ignored Exception:\n {}".format(e.message))
                sys.stderr.write(e.message)
        else:
            "Path {} isn't a directory. Doing Nothing.".format(dirname)

    def download(self):
        """
        Checks that bucket is available and downloads self.keyname to self.tarpath. 
        Then extracts self.tarpath to self.dirpath.
        """
        bucket = self.bucket(self.bucket_name)
        if not bucket:
            return
        
        self.download_dir(bucket, self.tarpath, self.dirpath, self.keyname)

    def upload(self):
        """
        Checks that bucket is available. Then compresses self.dirpath to self.tarpath
        and uploads self.tarpath to self.keyname.
        """
        bucket = self.bucket(self.bucket_name)
        if not bucket:
            return
        
        self.upload_dir(bucket, self.tarpath, self.dirpath, self.keyname)


def main():
    """
    Calls S3TarStore.upload or S3TarStore.download using the command line args.
    """
    parser = argparse.ArgumentParser(description='Upload/download tar.gz files to/from S3.')
    parser.add_argument('action', choices=('upload', 'download'))
    parser.add_argument('--bucket', '-b', dest='bucket_name', required=True,
                        help='Name of S3 bucket.')
    parser.add_argument('--folder', '-f', dest='bucket_folder', required=True,
                        help='Folder within S3 bucket. (ex. "v1/my-branch-name/")')
    parser.add_argument('--dir', '-d', dest='dirpath', required=True,
                        help='Directory to be uploaded from or downloaded to. '
                        '(ex. "~/.pip/download-cache/")')
    parser.add_argument('--tar', '-t', dest='tarpath', required=True,
                        help='Path to place newly created or downloaded tarfile. '
                        'The basename of this should be the basename of the tarfile '
                        'stored in S3. (ex. "~/pip-download-cache.tar.gz")')
    args = parser.parse_args()

    store = S3TarStore(
        dirpath = path(args.dirpath),
        tarpath = path(args.tarpath),
        bucket_name = args.bucket_name,
        bucket_folder = args.bucket_folder,
    )
    
    if args.action == 'upload':
        store.upload()
    elif args.action == 'download':
        store.download()


if __name__ == '__main__':
    main()
