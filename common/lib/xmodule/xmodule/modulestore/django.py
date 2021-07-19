"""
Module that provides a connection to the ModuleStore specified in the django settings.

Passes settings.MODULESTORE as kwargs to MongoModuleStore
"""

from importlib import import_module
import gettext
import logging

from pkg_resources import resource_filename
import re  # lint-amnesty, pylint: disable=wrong-import-order

from django.conf import settings

# This configuration must be executed BEFORE any additional Django imports. Otherwise, the imports may fail due to
# Django not being configured properly. This mostly applies to tests.
if not settings.configured:
    settings.configure()

from django.core.cache import caches, InvalidCacheBackendError  # lint-amnesty, pylint: disable=wrong-import-position
import django.dispatch  # lint-amnesty, pylint: disable=wrong-import-position
import django.utils  # lint-amnesty, pylint: disable=wrong-import-position
from django.utils.translation import get_language, to_locale  # lint-amnesty, pylint: disable=wrong-import-position
from edx_django_utils.cache import DEFAULT_REQUEST_CACHE, RequestCache  # lint-amnesty, pylint: disable=wrong-import-position

from xmodule.contentstore.django import contentstore  # lint-amnesty, pylint: disable=wrong-import-position
from xmodule.modulestore.draft_and_published import BranchSettingMixin  # lint-amnesty, pylint: disable=wrong-import-position
from xmodule.modulestore.mixed import MixedModuleStore  # lint-amnesty, pylint: disable=wrong-import-position
from xmodule.util.xmodule_django import get_current_request_hostname  # lint-amnesty, pylint: disable=wrong-import-position

# We also may not always have the current request user (crum) module available
try:
    from common.djangoapps.xblock_django.user_service import DjangoXBlockUserService
    from crum import get_current_user

    HAS_USER_SERVICE = True
except ImportError:
    HAS_USER_SERVICE = False

try:
    from common.djangoapps.xblock_django.api import disabled_xblocks
except ImportError:
    disabled_xblocks = None

log = logging.getLogger(__name__)
ASSET_IGNORE_REGEX = getattr(settings, "ASSET_IGNORE_REGEX", r"(^\._.*$)|(^\.DS_Store$)|(^.*~$)")


class SwitchedSignal(django.dispatch.Signal):
    """
    SwitchedSignal is like a normal Django signal, except that you can turn it
    on and off. This is especially useful for tests where we want to be able to
    isolate signals and disable expensive operations that are irrelevant to
    what's being tested (like everything that triggers off of a course publish).

    SwitchedSignals default to being on. You should be very careful if you ever
    turn one off -- the only instances of this class are shared class attributes
    of `SignalHandler`. You have to make sure that you re-enable the signal when
    you're done, or else you may permanently turn that signal off for that
    process. I can't think of any reason you'd want to disable signals outside
    of running tests.
    """
    def __init__(self, name, *args, **kwargs):
        """
        The `name` parameter exists only to make debugging more convenient.

        All other args are passed to the constructor for django.dispatch.Signal.
        """
        super().__init__(*args, **kwargs)
        self.name = name
        self._allow_signals = True

    def disable(self):
        """
        Turn off signal sending.

        All calls to send/send_robust will no-op.
        """
        self._allow_signals = False

    def enable(self):
        """
        Turn on signal sending.

        Calls to send/send_robust will behave like normal Django Signals.
        """
        self._allow_signals = True

    def send(self, *args, **kwargs):
        """
        See `django.dispatch.Signal.send()`

        This method will no-op and return an empty list if the signal has been
        disabled.
        """
        log.debug(
            "SwitchedSignal %s's send() called with args %s, kwargs %s - %s",
            self.name,
            args,
            kwargs,
            "ALLOW" if self._allow_signals else "BLOCK"
        )
        if self._allow_signals:
            return super().send(*args, **kwargs)
        return []

    def send_robust(self, *args, **kwargs):
        """
        See `django.dispatch.Signal.send_robust()`

        This method will no-op and return an empty list if the signal has been
        disabled.
        """
        log.debug(
            "SwitchedSignal %s's send_robust() called with args %s, kwargs %s - %s",
            self.name,
            args,
            kwargs,
            "ALLOW" if self._allow_signals else "BLOCK"
        )
        if self._allow_signals:
            return super().send_robust(*args, **kwargs)
        return []

    def __repr__(self):
        return f"SwitchedSignal('{self.name}')"


class SignalHandler:
    """
    This class is to allow the modulestores to emit signals that can be caught
    by other parts of the Django application. If your app needs to do something
    every time a course is published (e.g. search indexing), you can listen for
    that event and kick off a celery task when it happens.

    To listen for a signal, do the following::

        from django.dispatch import receiver
        from celery import shared_task
        from edx_django_utils.monitoring import set_code_owner_attribute
        from xmodule.modulestore.django import modulestore, SignalHandler

        @receiver(SignalHandler.course_published)
        def listen_for_course_publish(sender, course_key, **kwargs):
            do_my_expensive_update.delay(course_key)

        @shared_task()
        @set_code_owner_attribute
        def do_my_expensive_update(course_key):
            # ...

    Things to note:

    1. We receive using the Django Signals mechanism.
    2. The sender is going to be the class of the modulestore sending it.
    3. The names of your handler function's parameters *must* be "sender" and "course_key".
    4. Always have **kwargs in your signal handler, as new things may be added.
    5. The thing that listens for the signal lives in process, but should do
       almost no work. Its main job is to kick off the celery task that will
       do the actual work.
    """

    # If you add a new signal, please don't forget to add it to the _mapping
    # as well.
    pre_publish = SwitchedSignal("pre_publish", providing_args=["course_key"])
    course_published = SwitchedSignal("course_published", providing_args=["course_key"])
    course_deleted = SwitchedSignal("course_deleted", providing_args=["course_key"])
    library_updated = SwitchedSignal("library_updated", providing_args=["library_key"])
    item_deleted = SwitchedSignal("item_deleted", providing_args=["usage_key", "user_id"])

    _mapping = {
        signal.name: signal
        for signal
        in [pre_publish, course_published, course_deleted, library_updated, item_deleted]
    }

    def __init__(self, modulestore_class):
        self.modulestore_class = modulestore_class

    @classmethod
    def all_signals(cls):
        """Return a list with all our signals in it."""
        return cls._mapping.values()

    @classmethod
    def signal_by_name(cls, signal_name):
        """Given a signal name, return the appropriate signal."""
        return cls._mapping[signal_name]

    def send(self, signal_name, **kwargs):
        """
        Send the signal to the receivers.
        """
        signal = self._mapping[signal_name]
        responses = signal.send_robust(sender=self.modulestore_class, **kwargs)

        for receiver, response in responses:
            log.info('Sent %s signal to %s with kwargs %s. Response was: %s', signal_name, receiver, kwargs, response)


# to allow easy imports
globals().update({sig.name.upper(): sig for sig in SignalHandler.all_signals()})


def load_function(path):
    """
    Load a function by name.

    Arguments:
        path: String of the form 'path.to.module.function'. Strings of the form
            'path.to.module:Class.function' are also valid.

    Returns:
        The imported object 'function'.
    """
    if ':' in path:
        module_path, _, method_path = path.rpartition(':')
        module = import_module(module_path)

        class_name, method_name = method_path.split('.')
        _class = getattr(module, class_name)
        function = getattr(_class, method_name)
    else:
        module_path, _, name = path.rpartition('.')
        function = getattr(import_module(module_path), name)

    return function


def create_modulestore_instance(
        engine,
        content_store,
        doc_store_config,
        options,
        i18n_service=None,
        fs_service=None,
        user_service=None,
        signal_handler=None,
):
    """
    This will return a new instance of a modulestore given an engine and options
    """
    # Import is placed here to avoid model import at project startup.
    import xblock.reference.plugins

    class_ = load_function(engine)

    _options = {}
    _options.update(options)

    FUNCTION_KEYS = ['render_template']
    for key in FUNCTION_KEYS:
        if key in _options and isinstance(_options[key], str):
            _options[key] = load_function(_options[key])

    request_cache = DEFAULT_REQUEST_CACHE

    try:
        metadata_inheritance_cache = caches['mongo_metadata_inheritance']
    except InvalidCacheBackendError:
        metadata_inheritance_cache = caches['default']

    if issubclass(class_, MixedModuleStore):
        _options['create_modulestore_instance'] = create_modulestore_instance

    if issubclass(class_, BranchSettingMixin):
        _options['branch_setting_func'] = _get_modulestore_branch_setting

    if HAS_USER_SERVICE and not user_service:
        xb_user_service = DjangoXBlockUserService(get_current_user())
    else:
        xb_user_service = None

    xblock_field_data_wrappers = [load_function(path) for path in settings.XBLOCK_FIELD_DATA_WRAPPERS]

    def fetch_disabled_xblock_types():
        """
        Get the disabled xblock names, using the request_cache if possible to avoid hitting
        a database every time the list is needed.
        """
        # If the import could not be loaded, return an empty list.
        if disabled_xblocks is None:
            return []

        if 'disabled_xblock_types' not in request_cache.data:
            request_cache.data['disabled_xblock_types'] = [block.name for block in disabled_xblocks()]
        return request_cache.data['disabled_xblock_types']

    return class_(
        contentstore=content_store,
        metadata_inheritance_cache_subsystem=metadata_inheritance_cache,
        request_cache=request_cache,
        xblock_mixins=getattr(settings, 'XBLOCK_MIXINS', ()),
        xblock_select=getattr(settings, 'XBLOCK_SELECT_FUNCTION', None),
        xblock_field_data_wrappers=xblock_field_data_wrappers,
        disabled_xblock_types=fetch_disabled_xblock_types,
        doc_store_config=doc_store_config,
        i18n_service=i18n_service or ModuleI18nService,
        fs_service=fs_service or xblock.reference.plugins.FSService(),
        user_service=user_service or xb_user_service,
        signal_handler=signal_handler or SignalHandler(class_),
        **_options
    )


# A singleton instance of the Mixed Modulestore
_MIXED_MODULESTORE = None


class CachingModuleStoreWrapper:
    """
    Wrap a modulestore and add request-level caching of get_course()

    This class proxies most of its requests to its underlying Modulestore
    object. It was necessary to do this as a separate wrapping layer because
    our _MIXED_MODULESTORE can be a CCXModulestoreWrapper or a MixedModuleStore
    depending on our settings. Putting this caching into MixedModuleStore itself
    doesn't work because of the way CCXModulestoreWrapper pulls back results
    from MixedModuleStore and changes their usage keys.

    So yes, this means that content access is layered behind proxies like:

      CachingModuleStoreWrapper ->
        (CCXModulestoreWrapper -> if CCX enabled)
          MixedModuleStore ->
            DraftVersioningModuleStore (Split Mongo)
            DraftModuleStore (Old Mongo)

    The main thing we have to worry about in this class is to be able to detect
    any call that might potentially invalidate the cache course, and to do that
    invalidation before sending the call along.
    """
    def __init__(self, modulestore_obj):
        self.__dict__['_modulestore'] = modulestore_obj
        self.__dict__['_request_cache'] = RequestCache('CachingModulestoreWrapper')

    def __getattr__(self, name):
        """Look up missing attributes on the wrapped modulestore"""
        return getattr(self._modulestore, name)

    def __setattr__(self, name, value):
        """Set attributes only on the wrapped modulestore"""
        setattr(self._modulestore, name, value)

    def __delattr__(self, name):
        """Delete attributes only on the wrapped modulestore"""
        delattr(self._modulestore, name)

    def _remove_from_course_cache(self, course_key):
        """
        Remove all instances of this course_key from the local request cache.
        """
        # Remember that there may be multiple keys for the same course
        cache_keys_to_del = [
            cache_key
            for cache_key in self._request_cache.data
            if cache_key[0] == course_key  # cache_key is (course_key, depth)
        ]
        for cache_key in cache_keys_to_del:
            self._request_cache.delete(cache_key)

    def get_course(self, course_key, depth=0, **kwargs):
        """
        Call get_course on wrapped modulestore, but with request-caching.

        This is the only call that actually _uses_ caching at this layer.
        """
        # Only use the request cache if we're dealing with a simple query with
        # no advanced params. (This is the vast, vast majority of queries.)
        use_cache = not kwargs
        cache_key = (course_key, depth)
        if use_cache:
            cache_response = self._request_cache.get_cached_response(cache_key)
            if cache_response.is_found:
                return cache_response.value

        course = self._modulestore.get_course(course_key, depth, **kwargs)
        if use_cache:
            self._request_cache.set(cache_key, course)

        return course

    # Everything that follows are method calls that would cause cache
    # invalidation. Unfortunately, how we derive a course_key and when it's safe
    # to use varies by method, so there's a lot of boilerplate copying. Some of
    # these might not be necessary, but it's better to err on the side of
    # invalidation than risk correctness.

    def delete_course(self, course_key, user_id):
        result = self._modulestore.delete_course(course_key, user_id)
        self._remove_from_course_cache(course_key)
        return result

    def save_asset_metadata(self, asset_metadata, user_id, import_only=False):
        result = self._modulestore.save_asset_metadata(asset_metadata, user_id, import_only)
        self._remove_from_course_cache(asset_metadata.asset_id.course_key)
        return result

    def save_asset_metadata_list(self, asset_metadata_list, user_id, import_only=False):
        result = self.modulestore.save_asset_metadata_list(asset_metadata_list, user_id, import_only)
        if asset_metadata_list:
            self._remove_from_course_cache(asset_metadata_list[0].asset_id.course_key)
        return result

    def delete_asset_metadata(self, asset_key, user_id):
        result = self._modulestore.delete_asset_metadata(asset_key, user_id)
        self._remove_from_course_cache(asset_key.course_key)
        return result

    def copy_all_asset_metadata(self, source_course_key, dest_course_key, user_id):
        result = self._modulestore.copy_all_asset_metadata(source_course_key, dest_course_key, user_id)
        self._remove_from_course_cache(dest_course_key)
        return result

    def set_asset_metadata_attr(self, asset_key, attr, value, user_id):
        result = self._modulestore.set_asset_metadata_attr(asset_key, attr, value, user_id)
        self._remove_from_course_cache(asset_key.course_key)
        return result

    def set_asset_metadata_attrs(self, asset_key, attr_dict, user_id):
        result = self._modulestore.set_asset_metadata_attrs(asset_key, attr_dict, user_id)
        self._remove_from_course_cache(asset_key.course_key)
        return result

    def clone_course(self, source_course_id, dest_course_id, user_id, fields=None, **kwargs):
        result = self._modulestore.clone_course(source_course_id, dest_course_id, user_id, fields, **kwargs)
        self._remove_from_course_cache(dest_course_id)
        return result

    def create_item(self, user_id, course_key, block_type, block_id=None, fields=None, **kwargs):
        result = self._modulestore.create_item(user_id, course_key, block_type, block_id, fields, **kwargs)
        self._remove_from_course_cache(course_key)
        return result

    def create_child(self, user_id, parent_usage_key, block_type, block_id=None, fields=None, **kwargs):
        result = self._modulestore.create_child(user_id, parent_usage_key, block_type, block_id, fields, **kwargs)
        self._remove_from_course_cache(parent_usage_key.course_key)
        return result

    def import_xblock(self, user_id, course_key, block_type, block_id, fields=None, runtime=None, **kwargs):
        result = self._modulestore.import_xblock(user_id, course_key, block_type, block_id, fields, runtime, **kwargs)
        self._remove_from_course_cache(course_key)
        return result

    def copy_from_template(self, source_keys, dest_key, user_id, **kwargs):
        result = self._modulestore.copy_from_template(source_keys, dest_key, user_id, **kwargs)
        self._remove_from_course_cache(dest_key.course_key)
        return result

    def update_item(self, xblock, user_id, allow_not_found=False, **kwargs):
        result = self._modulestore.update_item(xblock, user_id, allow_not_found, **kwargs)
        self._remove_from_course_cache(xblock.location.course_key)
        return result

    def delete_item(self, location, user_id, **kwargs):
        result = self._modulestore.delete_item(location, user_id, **kwargs)
        self._remove_from_course_cache(location.course_key)
        return result

    def revert_to_published(self, location, user_id):
        result = self._modulestore.revert_to_published(location, user_id)
        self._remove_from_course_cache(location.course_key)
        return result

    def reset_course_to_version(self, course_key, version_guid, user_id):
        result = self._modulestore.reset_course_to_version(course_key, version_guid, user_id)
        self._remove_from_course_cache(course_key)
        return result

    def create_xblock(self, runtime, course_key, block_type, block_id=None, fields=None, **kwargs):
        result = self._modulestore.create_xblock(runtime, course_key, block_type, block_id, fields, **kwargs)
        self._remove_from_course_cache(course_key)
        return result

    def publish(self, location, user_id, **kwargs):
        result = self._modulestore.publish(location, user_id, **kwargs)
        self._remove_from_course_cache(location.course_key)
        return result

    def unpublish(self, location, user_id, **kwargs):
        result = self._modulestore.unpublish(location, user_id, **kwargs)
        self._remove_from_course_cache(location.course_key)
        return result

    def convert_to_draft(self, location, user_id):
        result = self._modulestore.convert_to_draft(location, user_id)
        self._remove_from_course_cache(location.course_key)
        return result

    def has_changes(self, xblock):
        # Intentionally clearing cache before the proxied call, in order to make
        # sure our cache can't affect the comparison being done in has_changes.
        self._remove_from_course_cache(xblock.location.course_key)
        return self._modulestore.has_changes(xblock)


def modulestore():
    """
    Returns the Mixed modulestore
    """
    global _MIXED_MODULESTORE  # pylint: disable=global-statement
    if _MIXED_MODULESTORE is None:
        _MIXED_MODULESTORE = create_modulestore_instance(
            settings.MODULESTORE['default']['ENGINE'],
            contentstore(),
            settings.MODULESTORE['default'].get('DOC_STORE_CONFIG', {}),
            settings.MODULESTORE['default'].get('OPTIONS', {})
        )

        if settings.FEATURES.get('CUSTOM_COURSES_EDX'):
            # TODO: This import prevents a circular import issue, but is
            # symptomatic of a lib having a dependency on code in lms.  This
            # should be updated to have a setting that enumerates modulestore
            # wrappers and then uses that setting to wrap the modulestore in
            # appropriate wrappers depending on enabled features.
            from lms.djangoapps.ccx.modulestore import CCXModulestoreWrapper
            _MIXED_MODULESTORE = CCXModulestoreWrapper(_MIXED_MODULESTORE)

    return CachingModuleStoreWrapper(_MIXED_MODULESTORE)


def clear_existing_modulestores():
    """
    Clear the existing modulestore instances, causing
    them to be re-created when accessed again.

    This is useful for flushing state between unit tests.
    """
    global _MIXED_MODULESTORE  # pylint: disable=global-statement
    _MIXED_MODULESTORE = None


class ModuleI18nService:
    """
    Implement the XBlock runtime "i18n" service.

    Mostly a pass-through to Django's translation module.
    django.utils.translation implements the gettext.Translations interface (it
    has ugettext, ungettext, etc), so we can use it directly as the runtime
    i18n service.

    """
    def __init__(self, block=None):
        """
        Attempt to load an XBlock-specific GNU gettext translator using the XBlock's own domain
        translation catalog, currently expected to be found at:
            <xblock_root>/conf/locale/<language>/LC_MESSAGES/<domain>.po|mo
        If we can't locate the domain translation catalog then we fall-back onto
        django.utils.translation, which will point to the system's own domain translation catalog
        This effectively achieves translations by coincidence for an XBlock which does not provide
        its own dedicated translation catalog along with its implementation.
        """
        self.translator = django.utils.translation
        if block:
            xblock_class = getattr(block, 'unmixed_class', block.__class__)
            xblock_resource = xblock_class.__module__
            xblock_locale_dir = 'translations'
            xblock_locale_path = resource_filename(xblock_resource, xblock_locale_dir)
            xblock_domain = 'text'
            selected_language = get_language()
            try:
                self.translator = gettext.translation(
                    xblock_domain,
                    xblock_locale_path,
                    [to_locale(selected_language if selected_language else settings.LANGUAGE_CODE)]
                )
            except OSError:
                # Fall back to the default Django translator if the XBlock translator is not found.
                pass

    def __getattr__(self, name):
        name = 'gettext' if name == 'ugettext' else name
        return getattr(self.translator, name)

    def strftime(self, *args, **kwargs):
        """
        A locale-aware implementation of strftime.
        """
        # This is the wrong place to import this function.  I'm putting it here
        # because the xmodule test suite can't import this module, because
        # Django is not available in that suite.  This function isn't called in
        # that suite, so this hides the import so the test won't fail.
        #
        # As I said, this is wrong.  But Cale says this code will soon be
        # refactored to a place that will be right, and the code can be made
        # right there.  If you are reading this comment after April 1, 2014,
        # then Cale was a liar.
        from common.djangoapps.util.date_utils import strftime_localized

        return strftime_localized(*args, **kwargs)


def _get_modulestore_branch_setting():
    """
    Returns the branch setting for the module store from the current Django request if configured,
    else returns the branch value from the configuration settings if set,
    else returns None

    The value of the branch setting is cached in a thread-local variable so it is not repeatedly recomputed
    """

    def get_branch_setting():
        """
        Finds and returns the branch setting based on the Django request and the configuration settings
        """
        branch = None
        hostname = get_current_request_hostname()
        if hostname:
            # get mapping information which is defined in configurations
            mappings = getattr(settings, 'HOSTNAME_MODULESTORE_DEFAULT_MAPPINGS', None)

            # compare hostname against the regex expressions set of mappings which will tell us which branch to use
            if mappings:
                for key in mappings:
                    if re.match(key, hostname):
                        return mappings[key]
        if branch is None:
            branch = getattr(settings, 'MODULESTORE_BRANCH', None)
        return branch

    # leaving this in code structured in closure-friendly format b/c we might eventually cache this (again)
    # using request_cache
    return get_branch_setting()
