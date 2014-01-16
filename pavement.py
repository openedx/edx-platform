import sys
sys.path.append('.')
from paver.setuputils import setup
from pavelib import prereqs, assets, django, docs

setup(
    name="OpenEdX",
    packages=['OpenEdX'],
    version="1.0",
    url="",
    author="OpenEdX",
    author_email=""
)
