from __future__ import print_function
from invoke import Collection

ns = Collection()


from . import assets
from . import bok_choy
from . import clean
from . import db
from . import docs
from . import i18n
from . import prereqs
from . import servers
from . import test


ns.add_collection(assets)
ns.add_collection(clean)
ns.add_collection(db)
ns.add_collection(docs)
ns.add_collection(i18n)
ns.add_collection(prereqs)
ns.add_collection(servers)
ns.add_collection(test)
