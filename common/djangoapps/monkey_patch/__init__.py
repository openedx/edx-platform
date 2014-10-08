"""
Monkey-patch the edX platform

Here be dragons (and simians!)

* USE WITH CAUTION *
No, but seriously, you probably never really want to make changes here.
This module contains methods to monkey-patch [0] the edx-platform.
Patches are to be applied as early as possible in the callstack
(currently lms/startup.py and cms/startup.py). Consequently, changes
made here will affect the entire platform.

That said, if you've decided you really need to monkey-patch the
platform (and you've convinced enough people that this is best
solution), kindly follow these guidelines:
    - Reference django_utils_translation.py for a sample implementation.
    - Name your module by replacing periods with underscores for the
      module to be patched:
        - patching 'django.utils.translation'
          becomes 'django_utils_translation'
        - patching 'your.module'
          becomes 'your_module'
    - Implement argumentless function wrappers in
      monkey_patch.your_module for the following:
        - is_patched
        - patch
        - unpatch
    - Add the following code where needed (typically cms/startup.py and
      lms/startup.py):
        ```
        from monkey_patch import your_module
        your_module.patch()
        ```
    - Write tests! All code should be tested anyway, but with code that
      patches the platform runtime, we must be extra sure there are no
      unintended consequences.

[0] http://en.wikipedia.org/wiki/Monkey_patch
"""
# Use this key to store a reference to the unpatched copy
__BACKUP_ATTRIBUTE_NAME = '__monkey_patch'


def is_patched(module, attribute_name):
    """
    Check if an attribute has been monkey-patched
    """
    attribute = getattr(module, attribute_name)
    return hasattr(attribute, __BACKUP_ATTRIBUTE_NAME)


def patch(module, attribute_name, attribute_replacement):
    """
    Monkey-patch an attribute

    A backup of the original attribute is preserved in the patched
    attribute (see: __BACKUP_ATTRIBUTE_NAME).
    """
    attribute = getattr(module, attribute_name)
    setattr(attribute_replacement, __BACKUP_ATTRIBUTE_NAME, attribute)
    setattr(module, attribute_name, attribute_replacement)
    return is_patched(module, attribute_name)


def unpatch(module, attribute_name):
    """
    Un-monkey-patch an attribute

    Restore a backup of the original attribute from the patched
    attribute, iff it exists (see: __BACKUP_ATTRIBUTE_NAME).

    Return boolean whether or not the attribute could be unpatched
    """
    was_patched = False
    attribute = getattr(module, attribute_name)
    if hasattr(attribute, __BACKUP_ATTRIBUTE_NAME):
        attribute_old = getattr(attribute, __BACKUP_ATTRIBUTE_NAME)
        setattr(module, attribute_name, attribute_old)
        was_patched = True
    return was_patched
