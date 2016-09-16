"""
WE'RE USING MIGRATIONS!

If you make changes to this model, be sure to create an appropriate migration
file and check it in at the same time as your model changes. To do that,

1. Go to the edx-platform dir
2. ./manage.py schemamigration instructor_task --auto description_of_your_change
3. Add the migration file created in edx-platform/lms/djangoapps/instructor_task/migrations/


ASSUMPTIONS: modules have unique IDs, even across different module_types

"""
from cStringIO import StringIO
from gzip import GzipFile
from uuid import uuid4
import csv
import json
import hashlib
import os.path
import urllib

from boto.s3.connection import S3Connection
from boto.s3.key import Key

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models, transaction

from xmodule_django.models import CourseKeyField


# define custom states used by InstructorTask
QUEUING = 'QUEUING'
PROGRESS = 'PROGRESS'


class InstructorTask(models.Model):
    """
    Stores information about background tasks that have been submitted to
    perform work by an instructor (or course staff).
    Examples include grading and rescoring.

    `task_type` identifies the kind of task being performed, e.g. rescoring.
    `course_id` uses the course run's unique id to identify the course.
    `task_key` stores relevant input arguments encoded into key value for testing to see
           if the task is already running (together with task_type and course_id).
    `task_input` stores input arguments as JSON-serialized dict, for reporting purposes.
        Examples include url of problem being rescored, id of student if only one student being rescored.

    `task_id` stores the id used by celery for the background task.
    `task_state` stores the last known state of the celery task
    `task_output` stores the output of the celery task.
        Format is a JSON-serialized dict.  Content varies by task_type and task_state.

    `requester` stores id of user who submitted the task
    `created` stores date that entry was first created
    `updated` stores date that entry was last modified
    """
    task_type = models.CharField(max_length=50, db_index=True)
    course_id = CourseKeyField(max_length=255, db_index=True)
    task_key = models.CharField(max_length=255, db_index=True)
    task_input = models.CharField(max_length=255)
    task_id = models.CharField(max_length=255, db_index=True)  # max_length from celery_taskmeta
    task_state = models.CharField(max_length=50, null=True, db_index=True)  # max_length from celery_taskmeta
    task_output = models.CharField(max_length=1024, null=True)
    requester = models.ForeignKey(User, db_index=True)
    created = models.DateTimeField(auto_now_add=True, null=True)
    updated = models.DateTimeField(auto_now=True)
    subtasks = models.TextField(blank=True)  # JSON dictionary

    def __repr__(self):
        return 'InstructorTask<%r>' % ({
            'task_type': self.task_type,
            'course_id': self.course_id,
            'task_input': self.task_input,
            'task_id': self.task_id,
            'task_state': self.task_state,
            'task_output': self.task_output,
        },)

    def __unicode__(self):
        return unicode(repr(self))

    @classmethod
    def create(cls, course_id, task_type, task_key, task_input, requester):
        """
        Create an instance of InstructorTask.
        """
        # create the task_id here, and pass it into celery:
        task_id = str(uuid4())

        json_task_input = json.dumps(task_input)

        # check length of task_input, and return an exception if it's too long:
        if len(json_task_input) > 255:
            fmt = 'Task input longer than 255: "{input}" for "{task}" of "{course}"'
            msg = fmt.format(input=json_task_input, task=task_type, course=course_id)
            raise ValueError(msg)

        # create the task, then save it:
        instructor_task = cls(
            course_id=course_id,
            task_type=task_type,
            task_id=task_id,
            task_key=task_key,
            task_input=json_task_input,
            task_state=QUEUING,
            requester=requester
        )
        instructor_task.save_now()

        return instructor_task

    @transaction.atomic
    def save_now(self):
        """
        Writes InstructorTask immediately, ensuring the transaction is committed.
        """
        self.save()

    @staticmethod
    def create_output_for_success(returned_result):
        """
        Converts successful result to output format.

        Raises a ValueError exception if the output is too long.
        """
        # In future, there should be a check here that the resulting JSON
        # will fit in the column.  In the meantime, just return an exception.
        json_output = json.dumps(returned_result)
        if len(json_output) > 1023:
            raise ValueError("Length of task output is too long: {0}".format(json_output))
        return json_output

    @staticmethod
    def create_output_for_failure(exception, traceback_string):
        """
        Converts failed result information to output format.

        Traceback information is truncated or not included if it would result in an output string
        that would not fit in the database.  If the output is still too long, then the
        exception message is also truncated.

        Truncation is indicated by adding "..." to the end of the value.
        """
        tag = '...'
        task_progress = {'exception': type(exception).__name__, 'message': unicode(exception.message)}
        if traceback_string is not None:
            # truncate any traceback that goes into the InstructorTask model:
            task_progress['traceback'] = traceback_string
        json_output = json.dumps(task_progress)
        # if the resulting output is too long, then first shorten the
        # traceback, and then the message, until it fits.
        too_long = len(json_output) - 1023
        if too_long > 0:
            if traceback_string is not None:
                if too_long >= len(traceback_string) - len(tag):
                    # remove the traceback entry entirely (so no key or value)
                    del task_progress['traceback']
                    too_long -= (len(traceback_string) + len('traceback'))
                else:
                    # truncate the traceback:
                    task_progress['traceback'] = traceback_string[:-(too_long + len(tag))] + tag
                    too_long = 0
            if too_long > 0:
                # we need to shorten the message:
                task_progress['message'] = task_progress['message'][:-(too_long + len(tag))] + tag
            json_output = json.dumps(task_progress)
        return json_output

    @staticmethod
    def create_output_for_revoked():
        """Creates standard message to store in output format for revoked tasks."""
        return json.dumps({'message': 'Task revoked before running'})


class ReportStore(object):
    """
    Simple abstraction layer that can fetch and store CSV files for reports
    download. Should probably refactor later to create a ReportFile object that
    can simply be appended to for the sake of memory efficiency, rather than
    passing in the whole dataset. Doing that for now just because it's simpler.
    """
    @classmethod
    def from_config(cls, config_name):
        """
        Return one of the ReportStore subclasses depending on django
        configuration. Look at subclasses for expected configuration.
        """
        storage_type = getattr(settings, config_name).get("STORAGE_TYPE")
        if storage_type.lower() == "s3":
            return S3ReportStore.from_config(config_name)
        elif storage_type.lower() == "localfs":
            return LocalFSReportStore.from_config(config_name)

    def _get_utf8_encoded_rows(self, rows):
        """
        Given a list of `rows` containing unicode strings, return a
        new list of rows with those strings encoded as utf-8 for CSV
        compatibility.
        """
        for row in rows:
            yield [unicode(item).encode('utf-8') for item in row]


class S3ReportStore(ReportStore):
    """
    Reports store backed by S3. The directory structure we use to store things
    is::

        `{bucket}/{root_path}/{sha1 hash of course_id}/filename`

    We might later use subdirectories or metadata to do more intelligent
    grouping and querying, but right now it simply depends on its own
    conventions on where files are stored to know what to display. Clients using
    this class can name the final file whatever they want.
    """
    def __init__(self, bucket_name, root_path):
        self.root_path = root_path

        conn = S3Connection(
            settings.AWS_ACCESS_KEY_ID,
            settings.AWS_SECRET_ACCESS_KEY
        )

        self.bucket = conn.get_bucket(bucket_name)

    @classmethod
    def from_config(cls, config_name):
        """
        The expected configuration for an `S3ReportStore` is to have a
        `GRADES_DOWNLOAD` dict in settings with the following fields::

            STORAGE_TYPE : "s3"
            BUCKET : Your bucket name, e.g. "reports-bucket"
            ROOT_PATH : The path you want to store all course files under. Do not
                        use a leading or trailing slash. e.g. "staging" or
                        "staging/2013", not "/staging", or "/staging/"

        Since S3 access relies on boto, you must also define `AWS_ACCESS_KEY_ID`
        and `AWS_SECRET_ACCESS_KEY` in settings.
        """
        return cls(
            getattr(settings, config_name).get("BUCKET"),
            getattr(settings, config_name).get("ROOT_PATH")
        )

    def key_for(self, course_id, filename):
        """Return the S3 key we would use to store and retrieve the data for the
        given filename."""
        hashed_course_id = hashlib.sha1(course_id.to_deprecated_string())

        key = Key(self.bucket)
        key.key = "{}/{}/{}".format(
            self.root_path,
            hashed_course_id.hexdigest(),
            filename
        )

        return key

    def store(self, course_id, filename, buff, config=None):
        """
        Store the contents of `buff` in a directory determined by hashing
        `course_id`, and name the file `filename`. `buff` is typically a
        `StringIO`, but can be anything that implements `.getvalue()`.

        This method assumes that the contents of `buff` are gzip-encoded (it
        will add the appropriate headers to S3 to make the decompression
        transparent via the browser). Filenames should end in whatever
        suffix makes sense for the original file, so `.txt` instead of `.gz`
        """
        key = self.key_for(course_id, filename)

        _config = config if config else {}

        content_type = _config.get('content_type', 'text/csv')
        content_encoding = _config.get('content_encoding', 'gzip')

        data = buff.getvalue()
        key.size = len(data)
        key.content_encoding = content_encoding
        key.content_type = content_type

        # Just setting the content encoding and type above should work
        # according to the docs, but when experimenting, this was necessary for
        # it to actually take.
        key.set_contents_from_string(
            data,
            headers={
                "Content-Encoding": content_encoding,
                "Content-Length": len(data),
                "Content-Type": content_type,
            }
        )

    def store_rows(self, course_id, filename, rows):
        """
        Given a `course_id`, `filename`, and `rows` (each row is an iterable of
        strings), create a buffer that is a gzip'd csv file, and then `store()`
        that buffer.

        Even though we store it in gzip format, browsers will transparently
        download and decompress it. Filenames should end in `.csv`, not `.gz`.
        """
        output_buffer = StringIO()
        gzip_file = GzipFile(fileobj=output_buffer, mode="wb")
        csvwriter = csv.writer(gzip_file)
        csvwriter.writerows(self._get_utf8_encoded_rows(rows))
        gzip_file.close()

        self.store(course_id, filename, output_buffer)

    def delete_file(self, course_id, filename):
        """
        Given the `course_id` and `filename` for the report, this method deletes the report
        """
        key = self.key_for(course_id, filename)
        self.bucket.delete_key(key)

    def links_for(self, course_id):
        """
        For a given `course_id`, return a list of `(filename, url)` tuples. `url`
        can be plugged straight into an href
        """
        course_dir = self.key_for(course_id, '')
        return [
            (key.key.split("/")[-1], key.generate_url(expires_in=300))
            for key in sorted(self.bucket.list(prefix=course_dir.key), reverse=True, key=lambda k: k.last_modified)
        ]


class LocalFSReportStore(ReportStore):
    """
    LocalFS implementation of a ReportStore. This is meant for debugging
    purposes and is *absolutely not for production use*. Use S3ReportStore for
    that. We use this in tests and for local development. When it generates
    links, it will make file:/// style links. That means you actually have to
    copy them and open them in a separate browser window, for security reasons.
    This lets us do the cheap thing locally for debugging without having to open
    up a separate URL that would only be used to send files in dev.
    """
    def __init__(self, root_path):
        """
        Initialize with root_path where we're going to store our files. We
        will build a directory structure under this for each course.
        """
        self.root_path = root_path
        if not os.path.exists(root_path):
            os.makedirs(root_path)

    @classmethod
    def from_config(cls, config_name):
        """
        Generate an instance of this object from Django settings. It assumes
        that there is a dict in settings named GRADES_DOWNLOAD and that it has
        a ROOT_PATH that maps to an absolute file path that the web app has
        write permissions to. `LocalFSReportStore` will create any intermediate
        directories as needed. Example::

            STORAGE_TYPE : "localfs"
            ROOT_PATH : /tmp/edx/report-downloads/
        """
        return cls(getattr(settings, config_name).get("ROOT_PATH"))

    def path_to(self, course_id, filename):
        """Return the full path to a given file for a given course."""
        return os.path.join(self.root_path, urllib.quote(course_id.to_deprecated_string(), safe=''), filename)

    def store(self, course_id, filename, buff, config=None):  # pylint: disable=unused-argument
        """
        Given the `course_id` and `filename`, store the contents of `buff` in
        that file. Overwrite anything that was there previously. `buff` is
        assumed to be a StringIO objecd (or anything that can flush its contents
        to string using `.getvalue()`).
        """
        full_path = self.path_to(course_id, filename)
        directory = os.path.dirname(full_path)
        if not os.path.exists(directory):
            os.mkdir(directory)

        with open(full_path, "wb") as f:
            f.write(buff.getvalue())

    def store_rows(self, course_id, filename, rows):
        """
        Given a course_id, filename, and rows (each row is an iterable of strings),
        write this data out.
        """
        output_buffer = StringIO()
        csvwriter = csv.writer(output_buffer)
        csvwriter.writerows(self._get_utf8_encoded_rows(rows))

        self.store(course_id, filename, output_buffer)

    def delete_file(self, course_id, filename):
        """
        Given the `course_id` and `filename` for the report, this method deletes the report
        """
        path = self.path_to(course_id, filename)
        os.remove(path)

    def links_for(self, course_id):
        """
        For a given `course_id`, return a list of `(filename, url)` tuples. `url`
        can be plugged straight into an href. Note that `LocalFSReportStore`
        will generate `file://` type URLs, so you'll need to copy the URL and
        open it in a new browser window. Again, this class is only meant for
        local development.
        """
        course_dir = self.path_to(course_id, '')
        if not os.path.exists(course_dir):
            return []
        files = [(filename, os.path.join(course_dir, filename)) for filename in os.listdir(course_dir)]
        files.sort(key=lambda (filename, full_path): os.path.getmtime(full_path), reverse=True)

        return [
            (filename, ("file://" + urllib.quote(full_path)))
            for filename, full_path in files
        ]
