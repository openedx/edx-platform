from boto.s3.connection import S3Connection
import os
import tarfile


class PyVenvStore():
    def  __init__(self, req_hash, *args, **kwargs):
        """
        Set up common vars.
        """
        self.req_hash = req_hash

        # Set define file/dir paths needed
        home_dir = os.path.expanduser('~')
        self.local_venv_dir =  os.environ.get('EDX_PLATFORM_VENV_DIR', home_dir)
        self.local_venv_basename = os.environ.get('EDX_PLATFORM_VENV_NAME', 'edx-venv')
        self.archive_filename = "{}_{}.tar.gz".format(self.local_venv_basename, req_hash)
        self.local_archive_path = os.path.join(home_dir, self.archive_filename)
        
        # Set up S3 connection to bucket
        conn = S3Connection()
        bucket_name = os.environ.get('EDX_PLATFORM_VENV_BUCKET', 'edx-platform-virtualenvs')
        self.bucket = conn.get_bucket(bucket_name)
        self.key = self.bucket.lookup(self.archive_filename)

    def extract(self):
        """
        Extracts the virtualenv from a tar.gz file in S3.
        """    
        print "Fetching compressed virtualenv."
        self.key.get_contents_to_filename(self.local_archive_path)
    
        print "Extracting virtualenv."
        with tarfile.open(self.local_archive_path, mode='r:gz') as tar:
            tar.extractall(path=self.local_venv_dir)

    def upload(self):
        """
        Saves the current virtualenv to a tar.gz file in S3.
        """
        print "Compressing virtualenv."
        with tarfile.open(self.local_archive_path, "w:gz") as tar:
            tar.add(
                os.path.join(self.local_venv_dir, self.local_venv_basename),
                arcname=self.local_venv_basename,
            )

        print "Uploading compressed virtualenv to S3."
        key = self.bucket.new_key(self.archive_filename)
        key.set_contents_from_filename(self.local_archive_path)
