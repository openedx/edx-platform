"""
Run pylint on the code
"""
from __future__ import print_function
import sys
from invoke import task
from invoke import run as sh
from path import path
from .utils import Env

def run_pylint(system, report_dir=None, flags=""):
    apps = [path(system)] + path("{system}/djangoapps".format(system=system)).glob("*")
    if system != 'lms':
        apps += path("{system}/lib".format(system=system)).glob("*")

    apps = [app.basename().stripext() for app in apps if not app.endswith(".pyc")]


    from pprint import pprint
    pprint(apps)


    pythonpath = "PYTHONPATH={system}:{system}/djangoapps:{system}/lib:common/djangoapps:common/lib".format(system=system)

    import ipdb
    ipdb.set_trace()
    sh("{pythonpath} pylint {flags} -f parseable {apps} | tee {report_dir}/pylint.report".format(pythonpath=pythonpath,
                                                                                                 flags=flags,
                                                                                                 apps=" ".join(apps),
                                                                                                 report_dir=report_dir,
                                                                                              ))
def run_pep8(system, report_dir=None):
    sh("pep8 {system} | tee {report_dir}/pep8.report")



for system in ['lms', 'cms', 'common']:
    report_dir = Env.REPO_ROOT/system




def main():
    run_pylint("cms")

if __name__ == '__main__':
    main()
