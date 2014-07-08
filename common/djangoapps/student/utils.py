# -*- coding: utf-8 -*-

from logging import getLogger

from django.conf import settings

try:
    from suds.client import Client
    from suds.wsse import Security, UsernameToken, Timestamp
    from suds import WebFault, MethodNotFound, ServiceNotFound
except ImportError:
    raise

LOGGER = getLogger(__name__)

def authentification_service():
    """
    Creacion de cliente de servicio de
    autentificacion en WS
    """
    try:
        client_auth = Client(settings.WS_CONFIG['ws_auth'])
    except ServiceNotFound:
        LOGGER.error("Could not connect to service {0}".format(WS_CONFIG['ws_prod']))
        return
    req_auth = client_auth.factory.create(settings.WS_CONFIG['method_permission'])
    req_auth.Cedula = settings.WS_CONFIG['identity']
    req_auth.Urlsw = settings.WS_CONFIG['ws_prod']
    try:
        response = client_auth.service.ValidarPermiso(req_auth)
    except WebFault, e:
        print e
        return False
    if response.TienePermiso == 'N':
        LOGGER.debug("Error: no tiene permisos, respuesta de WS: %s" % response.TienePermiso)
        return False    
    return response

def add_tokens(response, student_identity):
    """
    Agregar token de seguridad y de tiempo
    en header de WS
    """
    security = Security()
    token = UsernameToken(settings.WS_CONFIG['identity'])
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
    verificar en WS de Senescyt si el identificador
    @student_identity tiene registros
    """
    try:
        client_titulo = Client(settings.WS_CONFIG['ws_prod'])
    except ServiceNotFound:
        LOGGER.error("Could not connect to service {0}".format(WS_CONFIG['ws_prod']))
        return
    response = authentification_service()#cl_auth.factory.create(settings.WS_CONFIG['method_permission'])
    if not response:
        return
    security = add_tokens(response, student_identity)
    client_titulo.set_options(wsse=security)
    LOGGER.debug("Consulta de titulo universitario de identificador: {0}".format(student_identity))
    consulta_response = client_titulo.service.consultaTitulo(arg0=student_identity)
    if not consulta_response:
        return
    nombre = consulta_response.nombre
    flag = False
    titulo = False
    numero = False
    for tit in consulta_response.niveltitulos:
        for ti in tit.titulo:
            titulo = ti.nombreTitulo
            numero_senescyt = ti.numeroRegistro
            flag = True
        if flag:
            break
    return {'nombre': nombre, 'number_senescyt': numero_senescyt, 'result': True}


    
