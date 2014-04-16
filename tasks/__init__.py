from __future__ import print_function
from invoke import Collection

ns = Collection()

import prereqs
import quality
import assets
import i18n
import servers
import docs

ns.add_collection(prereqs)
ns.add_collection(i18n)
ns.add_collection(servers)
ns.add_collection(assets)
ns.add_collection(quality)
ns.add_collection(docs)
