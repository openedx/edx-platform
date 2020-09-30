from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'third_party_auth.saml_configuration.tests.test_saml_configuration')

from common.djangoapps.third_party_auth.saml_configuration.tests.test_saml_configuration import *
