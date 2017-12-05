"""
tasks for controlling the databases used in tests
"""
from __future__ import print_function
import os

from paver.easy import sh, needs

from pavelib.utils.passthrough_opts import PassthroughTask
from pavelib.utils.timer import timed
from pavelib.utils.envs import Env


@needs('pavelib.prereqs.install_prereqs')
@PassthroughTask
@timed
def update_bokchoy_db_cache():
    """
    Update and cache the MYSQL database for bokchoy testing. This command
    will remove any previously cached database files and apply migrations
    on a fresh db.

    You can commit the resulting files in common/test/db_cache into
    git to speed up test runs
    """
    bokchoy_db_files = [
        'bok_choy_data_default.json',
        'bok_choy_data_student_module_history.json',
        'bok_choy_migrations_data_default.sql',
        'bok_choy_migrations_data_student_module_history.sql',
        'bok_choy_schema_default.sql',
        'bok_choy_schema_student_module_history.sql'
    ]
    print('Removing cached db files for bokchoy tests')
    for db_file in bokchoy_db_files:
        try:
            db_file_path = os.path.join(
                '{}/common/test/db_cache'.format(Env.REPO_ROOT), db_file
            )
            os.remove(db_file_path)
            print('\tRemoved {}'.format(db_file_path))
        except OSError:
            continue

    sh('{}/scripts/reset-test-db.sh'.format(Env.REPO_ROOT))
