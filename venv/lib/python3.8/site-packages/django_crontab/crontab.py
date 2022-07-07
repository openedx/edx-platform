from __future__ import print_function

import fcntl
import hashlib
import json
import logging
import os
import tempfile
import sys

from importlib import import_module

from django.conf import settings

from django_crontab.app_settings import Settings

string_type = basestring if sys.version_info[0] == 2 else str  # flake8: noqa

logger = logging.getLogger(__name__)


class Crontab(object):

    def __init__(self, **options):
        self.verbosity = int(options.get('verbosity', 1))
        self.readonly = options.get('readonly', False)
        self.crontab_lines = []
        self.settings = Settings(settings)

    def __enter__(self):
        """
        Automatically read crontab when used as with statement
        """
        self.read()
        return self

    def __exit__(self, type, value, traceback):
        """
        Automatically write back crontab when used as with statement if readonly is False
        """
        if not self.readonly:
            self.write()

    def read(self):
        """
        Reads the crontab into internal buffer
        """
        self.crontab_lines = os.popen('%s -l' % self.settings.CRONTAB_EXECUTABLE).readlines()

    def write(self):
        """
        Writes internal buffer back to crontab
        """
        fd, path = tempfile.mkstemp()
        tmp = os.fdopen(fd, 'w')
        for line in self.crontab_lines:
            tmp.write(line)
        tmp.close()
        os.system('%s %s' % (self.settings.CRONTAB_EXECUTABLE, path))
        os.unlink(path)

    def add_jobs(self):
        """
        Adds all jobs defined in CRONJOBS setting to internal buffer
        """
        for job in self.settings.CRONJOBS:
            # differ format and find job's suffix
            if len(job) > 2 and isinstance(job[2], string_type):
                # format 1 job
                job_suffix = job[2]
            elif len(job) > 4:
                job_suffix = job[4]
            else:
                job_suffix = ''

            self.crontab_lines.append(self.settings.CRONTAB_LINE_PATTERN % {
                'time': job[0],
                'comment': self.settings.CRONTAB_COMMENT,
                'command': ' '.join(filter(None, [
                    self.settings.COMMAND_PREFIX,
                    self.settings.PYTHON_EXECUTABLE,
                    self.settings.DJANGO_MANAGE_PATH,
                    'crontab', 'run',
                    self.__hash_job(job),
                    '--settings=%s' % self.settings.DJANGO_SETTINGS_MODULE if self.settings.DJANGO_SETTINGS_MODULE else '',
                    job_suffix,
                    self.settings.COMMAND_SUFFIX
                ]))
            })
            if self.verbosity >= 1:
                print('  adding cronjob: (%s) -> %s' % (self.__hash_job(job), job))

    def show_jobs(self):
        """
        Print the jobs from from crontab
        """
        print(u'Currently active jobs in crontab:')
        for line in self.crontab_lines[:]:
            job = self.settings.CRONTAB_LINE_REGEXP.findall(line)
            if job and job[0][4] == self.settings.CRONTAB_COMMENT:
                if self.verbosity >= 1:
                    print(u'%s -> %s' % (
                        job[0][2].split()[4],
                        self.__get_job_by_hash(job[0][2][job[0][2].find('crontab run') + 12:].split()[0])
                    ))

    def remove_jobs(self):
        """
        Removes all jobs defined in CRONJOBS setting from internal buffer
        """
        for line in self.crontab_lines[:]:
            job = self.settings.CRONTAB_LINE_REGEXP.findall(line)
            if job and job[0][4] == self.settings.CRONTAB_COMMENT:
                self.crontab_lines.remove(line)
                if self.verbosity >= 1:
                    print('removing cronjob: (%s) -> %s' % (
                        job[0][2].split()[4],
                        self.__get_job_by_hash(job[0][2][job[0][2].find('crontab run') + 12:].split()[0])
                    ))

    # noinspection PyBroadException
    def run_job(self, job_hash):
        """
        Executes the corresponding function defined in CRONJOBS
        """
        job = self.__get_job_by_hash(job_hash)
        job_name = job[1]
        job_args = job[2] if len(job) > 2 and not isinstance(job[2], string_type) else []
        job_kwargs = job[3] if len(job) > 3 else {}

        lock_file_name = None
        if self.settings.LOCK_JOBS:
            lock_file = open(os.path.join(tempfile.gettempdir(), 'django_crontab_%s.lock' % job_hash), 'w')
            lock_file_name = lock_file.name
            try:
                fcntl.flock(lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                logger.warning('Tried to start cron job %s that is already running.', job)
                return

        module_path, function_name = job_name.rsplit('.', 1)
        module = import_module(module_path)
        func = getattr(module, function_name)
        try:
            func(*job_args, **job_kwargs)
        except:
            logger.exception('Failed to complete cronjob at %s', job)

        if self.settings.LOCK_JOBS:
            try:
                fcntl.flock(lock_file, fcntl.LOCK_UN)
            except IOError:
                logger.exception('Error unlocking %s', lock_file_name)
                return

    def __hash_job(self, job):
        """
        Builds an md5 hash representing the job
        """
        j = json.JSONEncoder(sort_keys=True).encode(job)
        h = hashlib.md5(j.encode('utf-8')).hexdigest()
        return h

    def __get_job_by_hash(self, job_hash):
        """
        Finds the job by given hash
        """
        for job in self.settings.CRONJOBS:
            if self.__hash_job(job) == job_hash:
                return job
        raise RuntimeError(
            'No job with hash %s found. It seems the crontab is out of sync with your settings.CRONJOBS. '
            'Run "python manage.py crontab add" again to resolve this issue!' % job_hash
        )

