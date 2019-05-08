"""
Provide names as exported by older mongo.py module
"""

from __future__ import absolute_import

from xmodule.modulestore.mongo.base import MongoKeyValueStore, MongoModuleStore
# Backwards compatibility for prod systems that refererence
# xmodule.modulestore.mongo.DraftMongoModuleStore
from xmodule.modulestore.mongo.draft import DraftModuleStore as DraftMongoModuleStore
