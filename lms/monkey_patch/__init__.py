"""
Monkey Patch for slow Django Migrations taken from
https://github.com/cfpb/cfgov-refresh/commit/7616c6bb3ec310e72b1c9538d9176ba61a73ebd3#diff-dffeeb550eca65d51cda43001ff38d4d
"""

from __future__ import absolute_import

from django import VERSION
from django.db.migrations import executor, migration

from lms.monkey_patch.django import Django19MigrationExecutor


if VERSION[:2] < (1, 9):
    executor.MigrationExecutor = Django19MigrationExecutor
    migration.Migration.initial = None
