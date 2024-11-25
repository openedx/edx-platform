from cms.envs.test import *

# Fix MongoDb connection credentials
DOC_STORE_CONFIG["user"] = None
DOC_STORE_CONFIG["password"] = None