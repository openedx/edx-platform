"""
Run quality checkers on the code
"""
from __future__ import print_function

import sys
import argparse
from invoke import Collection,task

def run_pylint(system):
    print("running pylint on: %s" % system)

pylint = Collection("pylint")

for system in ('lms','cms','common'):

    @task(name = system)
    def pylint_system(system = system):
        return run_pylint(system)

    pylint.add_task(pylint_system,name = system)

tasks = Collection("quality")
tasks.add_collection(pylint)

