from xmodule.modulestore.django import modulestore, ModuleI18nService
from xmodule.x_module import ModuleSystem
from xblock.exceptions import NoSuchServiceError


class ModuleSystemLayer(ModuleSystem):  # pylint: disable=abstract-method
    """
    An XModule ModuleSystem for use in Studio previews
    """
    # xmodules can check for this attribute during rendering to determine if
    # they are being rendered for preview (i.e. in Studio)
    is_author_mode = True

    def __init__(self, **kwargs):
        services = kwargs.setdefault('services', {})
        services['i18n'] = None  # This key overrides super, populated on-demand by service() below
        super(ModuleSystemLayer, self).__init__(**kwargs)

    def service(self, block, service_name):
        """
        Runtime-specific override for the XBlock service manager.  If a service is not currently
        instantiated and is declared as a critical requirement, an attempt is made to load the
        module.

        Arguments:
            block (an XBlock): this block's class will be examined for service
                decorators.
            service_name (string): the name of the service requested.

        Returns:
            An object implementing the requested service, or None.
        """
        try:
            service = super(ModuleSystemLayer, self).service(block=block, service_name=service_name)
        except NoSuchServiceError:
            service_map = {
                'i18n': ModuleI18nService,
            }

            if block.service_declaration(service_name) == "need" and service_map.get(service_name, None):
                service = service_map[service_name](block)
            else:
                raise NoSuchServiceError("Service {!r} is not available.".format(service_name))

        return service
