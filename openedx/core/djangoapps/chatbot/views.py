import json
import logging
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from .models import ChatbotSession, ChatbotQuery
from .serializer import chatbot_query_list_serializer, chatbot_query_serializer, chatbot_session_list_serializer
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _
import requests
from .api import CHATBOT_QUERY_API, CHATBOT_BEARER_TOKEN

@require_http_methods('GET')
@login_required
def chatbot_fetch_query_list_view(request, session_id, skip, limit):
    user = request.user

    if session_id == '0':
        sessions = ChatbotSession.objects.filter(student=request.user).all()
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        print('STILL OK HERE')
        # query_list = [] if len(last_session) == 0 else last_session[-1].chatbot_queries.all()
        print(sessions)
        query_list = []
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
        print('STILL OK HERE -------------------------------------------------------')
    else:
        print('SESSION ID IS NOT 0')
        print('SESSION ID IS NOT 0')
        print('SESSION ID IS NOT 0')
        print('SESSION ID IS NOT 0')
        print('SESSION ID IS NOT 0')

        query_list = ChatbotQuery.objects.filter(session__student=user, session__id=session_id)

    print('SEEM OK')
    print('SEEM OK')
    print('SEEM OK')
    print('SEEM OK')
    print('SEEM OK')
    return JsonResponse(
        {
            'message': _('success'),
            'data': {
                'query_list': chatbot_query_list_serializer(query_list)
            }
        }, 
        status=200
    )

@require_http_methods('GET')
@login_required
def chatbot_fetch_session_list_view(request, session_id, skip, limit):
    user = request.user

    session_list = ChatbotQuery.objects.filter(student=user)

    return JsonResponse(
        {
            'message': _('success'),
            'data': {
                'session_list': chatbot_session_list_serializer(session_list)
            }
        }, 
        status=200
    )


@require_http_methods('POST')
@login_required
def chatbot_query_view(request):
    """
    Gửi query đến chatbot
    """
    user = request.user

    request_data = json.loads(request.body.decode('utf8'))

    query_msg = request_data.get('query_msg')
    session_id = request_data.get('session_id')

    session = ChatbotSession.objects.filter(session_id=session_id).first()

    if session is None: 
        return JsonResponse(
            {
                'message': _('Not found session'),
            }, 
            status=400
        )


    try:
        created_query = ChatbotQuery.objects.create(session=session, student=user, query_msg=query_msg)
    except Exception as e:
        logging.error(str(e))
        return JsonResponse(
            {
                'message': _('Internal Server Error'),
            }, 
            status=500
        )

    response_msg = _chatbot_get_response(query_msg, session_id)
    if response_msg is None: 
        created_query.status = 'failed'
        return JsonResponse(
            {
                'message': _('Failed'),
            }, 
            status=500
        )

    created_query.status = 'succeeded'
    created_query.response_msg = response_msg
    return JsonResponse(
        {
            'message': _('success'),
            'data': chatbot_query_serializer(created_query)
        }, 
        status=200
    )

@require_http_methods('PUT')
@login_required
def chatbot_vote_response_view(request):
    data = json.loads(request.body.decode('utf8'))

    if data.get('vote') not in ['up', 'down']:
        return JsonResponse(
            {
                'message': _('Vote must be "up" or "down"')
            },
            status=200
        )
        
    response = ChatbotQuery.objects.filter(id=data.get('query_id')).first()
    if resopnse is None: 
        return JsonResponse(
            {
                'message': _('Not found query response')
            },
            status=400
        )
    response.vote = data.get('vote')

    return JsonResponse(
        {
            'message': _('success'),  
            'data': {
                'vote': data.get('vote'),
                'query_id': data.get('query_id')
            }
        }
    )
    
@require_http_methods('POST')
@login_required
def chatbot_start_new_session_view(request):
    try:
        new_session = ChatbotSession.objects.create(student=request.user)
        return JsonResponse(
            {
                'message': _('success'), 
                'data': {
                    'session_id': new_session.session_id
                }
            },
            status=200
        )
    except Exception as e:
        logging.error(str(e))
        return JsonResponse(
            {
                'message': _('Internal Server Error')
            },
            status=500
        )

@require_http_methods('PUT')
@login_required
def chatbot_retry_query_view(request):
    data = json.loads(request.body.decode('utf8'))

    query = ChatbotQuery.objects.filter(id=data.get('query_id')).first()

    if query is None:
        return JsonRespone(
            {
                'message': _('Not found query')
            },
            status=400
        )
    
    if query.status != 'failed':
        return JsonRespone(
            {
                'message': _('You can only retry on failed query')
            },
            status=400
        )
    
    response_msg = _chatbot_get_response(query.query_msg, query.session.id)

    if response_msg is None: 
        query.status = 'failed'
        return JsonRespone(
            {
                'message': _('Internal Server Error')
            },
            status=500
        )

    query.status == 'succeeded'
    query.response_msg = response_msg
    return JsonRespone(
        {
            'message': _('success'),
            'data': {
                'id': query
            }
        },
        status=200
    )


@require_http_methods('PUT')
@login_required
def chatbot_cancel_query_view(request):
    data = json.loads(request.body.decode('utf8'))

    query = ChatbotQuery.objects.filter(id=data.get('query_id')).first()

    if query is None:
        return JsonRespone(
            {
                'message': _('Not found query')
            },
            status=400
        )
    
    if query.status != 'pending':
        return JsonRespone(
            {
                'message': _('This query has already finished')
            },
            status=400
        )

    query.status = 'canceled'
    return JsonRespone(
        {
            'message': _('success')
        },
        status=200
    )


# helper function
def _chatbot_get_response(query_msg, session_id):
    url = CHATBOT_QUERY_API
    headers = {
        'Content-Type': 'application/json', 
        'Authorization': f'Bearer {CHATBOT_BEARER_TOKEN}'
    }
    data = {
        'query': query_msg,
        'chat_id': session_id
    }

    r = requests.post(url, headers=headers, data=data)

    if r.status_code == 200:
        return r.json()
    
    return None