"""
LMS Interface to external queueing system (xqueue)
"""
from typing import Dict, Optional, TYPE_CHECKING

import hashlib
import json
import logging

import requests
from django.conf import settings
from django.urls import reverse
from requests.auth import HTTPBasicAuth
import re
from xmodule.capa.util import construct_callback
if TYPE_CHECKING:
    from xmodule.capa_block import ProblemBlock

log = logging.getLogger(__name__)
dateformat = '%Y-%m-%dT%H:%M:%S'


XQUEUE_METRIC_NAME = 'edxapp.xqueue'

# Wait time for response from Xqueue.
XQUEUE_TIMEOUT = 35  # seconds
CONNECT_TIMEOUT = 3.05  # seconds
READ_TIMEOUT = 10  # seconds




def extract_item_data(header, payload):
    # Convertir header de JSON a diccionario si es necesario
    if isinstance(header, str):
        try:
            header = json.loads(header)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al decodificar header: {e}")

    # Convertir payload de JSON a diccionario si es necesario
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error al decodificar payload: {e}")

    # Extraer callback_url
    callback_url = header.get('lms_callback_url')
    if not callback_url:
        raise ValueError("El header no contiene 'lms_callback_url'.")

    # Extraer datos del callback_url con validaciones
    match_item_id = re.search(r'block@([^/]+)', callback_url)
    match_item_type = re.search(r'type@([^+]+)', callback_url)
    match_course_id = re.search(r'course-v1:([^/]+)', callback_url)

    if not (match_item_id and match_item_type and match_course_id):
        raise ValueError(f"El formato de callback_url no es válido: {callback_url}")

    item_id = match_item_id.group(1)
    item_type = match_item_type.group(1)
    course_id = match_course_id.group(1)

    # Decodificar student_info
    try:
        student_info = json.loads(payload["student_info"])
    except json.JSONDecodeError as e:
        raise ValueError(f"Error al decodificar student_info: {e}")

    student_id = student_info.get("anonymous_student_id")
    if not student_id:
        raise ValueError("El campo 'anonymous_student_id' no está presente en student_info.")

    # Construir el diccionario de resultados
    student_dict = {
        'item_id': item_id,
        'item_type': item_type,
        'course_id': course_id,
        'student_id': student_id
    }

    # Obtener la respuesta del estudiante
    student_answer = payload.get("student_response")
    if student_answer is None:
        raise ValueError("El campo 'student_response' no está presente en payload.")

    return student_dict, student_answer

class XQueueInterfaceSubmission:
    """
    Interface to the external grading system
    """

    def __init__(self, url: str, django_auth: Dict[str, str], requests_auth: Optional[HTTPBasicAuth] = None):
        self.url = url
        self.auth = django_auth
        self.session = requests.Session()
        self.session.auth = requests_auth
        
    

    def send_to_submission(self, header, body, files_to_upload=None):
        from submissions.api import create_submission
        try:
            # Extraer datos del item
            student_item, answer = extract_item_data(header, body)
            print("student_item -------------------------------------------------- ", student_item)
            
            # Llamar a create_submission
            submission = create_submission(student_item, answer)
            print("submission -------------------------------------------------- ", submission)
            
            # Retornar éxito
            return (0, "Submission sent successfully")
        except Exception as e:
            # Retornar error con mensaje de la excepción
            return (1, f"Error: {str(e)}")
        # Asegurar que siempre se devuelve una tupla
        return (1, "Unknown error")

