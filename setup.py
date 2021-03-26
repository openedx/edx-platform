import setuptools
from setuptools import find_packages, find_namespace_packages

setuptools.setup(
    packages=(
        find_namespace_packages(include=['lms*']) +
        find_packages(include=['cms*', 'openedx*', 'common.djangoapps.*']) +
        find_packages(include=['capa*'], where='common/lib/capa', exclude=["tests"]) +
        find_packages(include=['safe_lxml*'], where='common/lib/safe_lxml') +
        find_packages(include=['symmath*'], where='common/lib/symmath') +
        find_packages(include=['xmodule*'], where='common/lib/xmodule', exclude=["tests"]) +
        find_packages(include=['loncapa*'], where='common/lib/sandbox-packages') +
        find_packages(include=['verifiers*'], where='common/lib/sandbox-packages') +
        find_packages(include=['eia*'], where='common/lib/sandbox-packages')
    ),
    package_dir={
        "": ".",
        "capa": "common/lib/capa/capa",
        "safe_lxml": "common/lib/safe_lxml/safe_lxml",
        "loncapa": "common/lib/sandbox-packages/loncapa",
        "verifiers": "common/lib/sandbox-packages/verifiers",
        "eia": "common/lib/sandbox-packages/eia",
        "symmath": "common/lib/symmath/symmath",
        "xmodule": "common/lib/xmodule/xmodule",
    },
)
