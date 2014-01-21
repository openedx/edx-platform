# -*- coding: utf-8 -*-

from logging import getLogger

from django.config import settings

try:
    from suds.client import Client
    from suds.wsse import Security, UsernameToken, Timestamp
    from suds import WebFault, MethodNotFound, ServiceNotFound
except ImportError:
    raise

LOGGER = getLogger(__name__)

def authentification_service():
    """
    TODO:
    """
    try:
        client_auth = Client(settings.WS_CONFIG['ws_auth'])
    except ServiceNotFound:
        LOGGER.error("Could not connect to service {0}".format(WS_CONFIG['ws_prod']))
        return
    req_auth = cl_auth.factory.create(settings.WS_CONFIG['method_permission'])
    req_auth.Cedula = student_identity
    req_auth.Urlsw = WS_CONFIG['ws_prod']
    try:
        response = cl_auth.service.ValidarPermiso(req_auth)
    except WebFault, e:
        print e
        return False
    if response.TienePermiso == 'N':
        LOGGER.debug("Error: no tiene permisos, respuesta de WS: %s" % response.TienePermiso)
        return False    
    return response

def add_tokens(response, student_identity):
    security = Security()
    token = UsernameToken(student_identity)
    token.setcreated(response.Fecha)
    token.nonce_has_encoding = True
    token.setnonce(response.Nonce)
    token.setpassworddigest(response.Digest)
    security.tokens.append(token)
    token_ts = Timestamp()
    token_ts.created = response.Fecha
    token_ts.expires = response.FechaF
    security.tokens.append(token_ts)
    return security

def verify_academic_student(student_identity):
    """
    TODO:
    """
    try:
        client_titulo = Client(settings.WS_CONFIG['ws_prod'])
    except ServiceNotFound:
        LOGGER.error("Could not connect to service {0}".format(WS_CONFIG['ws_prod']))
        return
#    try:
#        client_auth = Client(settings.WS_CONFIG['ws_auth'])
#    except ServiceNotFound:
#        LOGGER.error("Could not connect to service {0}".format(WS_CONFIG['ws_prod']))
#        return
    response = authentification_service()#cl_auth.factory.create(settings.WS_CONFIG['method_permission'])
#    req_auth.Cedula = student_identity
#    req_auth.Urlsw = WS_CONFIG['ws_prod']
#    response = cl_auth.service.ValidarPermiso(req_auth)
#    if response.TienePermiso == 'N':
#        LOGGER.debug("Error: no tiene permisos, respuesta de WS: %s" % response.TienePermiso)
#        return False
    if not response:
        return
    security = add_tokens(response, student_identity)
#    security = Security()
#    token = UsernameToken(student_identity)
#    token.setcreated(response.Fecha)
#    token.nonce_has_encoding = True
#    token.setnonce(response.Nonce)
#    token.setpassworddigest(response.Digest)
#    security.tokens.append(token)
#    token_ts = Timestamp()
#    token_ts.created = response.Fecha
#    token_ts.expires = response.FechaF
#    security.tokens.append(token_ts)
    client.set_options(wsse=security)
    consulta_response = client.service.consultaTitulo(arg0=student_identity)
    LOGGER.debug("Consulta de titulo universitario de identificador: {0}".format(consulta_response.cedula))
    for t in consulta_response:
        print t[0], t[1]

    
