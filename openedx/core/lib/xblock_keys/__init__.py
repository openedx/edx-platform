"""
Conveniently allow importing all of edx-platforms new key types.

We'll probably move these into the opaque-keys repository once
they new key formats stabilize.
"""
from .bundle_def import BundleDefinitionLocator
from .learning_context_key import LearningContextKey, GlobalContextLocator, global_context
from .usage_locator import GlobalUsageLocator
