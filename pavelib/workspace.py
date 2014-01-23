# Run --- Internationalization tasks

from paver.easy import *
from pavelib import assets
import os


@task
def workspace_migrate():
    """
    Run scripts in ws_migrations directory
    """

    MIGRATION_MARKER_DIR = os.path.join(assets.REPO_ROOT, '.ws_migrations_complete')
    MIGRATION_DIR = os.path.join(assets.REPO_ROOT, 'ws_migrations')
    SKIP_MIGRATIONS = os.getenv('SKIP_WS_MIGRATIONS', False)

    if SKIP_MIGRATIONS:
        return

    files = os.listdir(MIGRATION_DIR)

    migration_files = []

    for file in files:
        if not file == 'README.rst' and os.access(file, os.X_OK):
            migration_files.append(file)

    for migration in migration_files:
        completion_file = os.path.join(MIGRATION_MARKER_DIR, os.path.basename(migration))
        if not os.path.isfile(completion_file):
            cmd = os.path.join(MIGRATION_DIR, migration)
            sh(cmd)
            open(completion_file, 'w')
