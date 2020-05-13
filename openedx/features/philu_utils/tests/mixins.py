from openedx.core.djangolib.testing.philu_utils import clear_philu_theme, configure_philu_theme


class PhiluThemeMixin(object):
    """Mixin class for PhilU site and site theme"""

    @classmethod
    def setUpClass(cls):
        super(PhiluThemeMixin, cls).setUpClass()
        configure_philu_theme()

    @classmethod
    def tearDownClass(cls):
        clear_philu_theme()
        super(PhiluThemeMixin, cls).tearDownClass()
