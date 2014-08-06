from .common import *

FEATURES['ENABLE_CREATOR_GROUP'] = True
TIME_ZONE = 'America/Guayaquil'
LANGUAGE_CODE = 'es-419'
USE_I18N = True
USE_L10N = True

INSTALLED_APPS += ('cities',)

DELTA_YEAR = 12
MAX_YEAR_ALLOWED = 70

########################## WS CONFIG ###########################

WS_CONFIG = {
    'ws_prod': "https://www.bsg.gob.ec/sw/SENESCYT/BSGSW01_Consultar_Titulos?wsdl",
    'ws_auth': "https://www.bsg.gob.ec/sw/STI/BSGSW08_Acceder_BSG?wsdl",
    'method_permission': "validarPermisoPeticion",
    'method_query_title': "consultaTitulo",
    'identity': '0103893954'
    }
