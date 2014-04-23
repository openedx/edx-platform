from __future__ import print_function
from invoke import Collection

ns = Collection()

from .quality import tasks as quality_tasks

ns.add_collection(quality_tasks,"quality")