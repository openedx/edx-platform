from sys_path_hacks.warn import warn_deprecated_import

warn_deprecated_import('common.djangoapps', 'third_party_auth.samlproviderconfig.tests.test_samlproviderconfig')

from common.djangoapps.third_party_auth.samlproviderconfig.tests.test_samlproviderconfig import *
