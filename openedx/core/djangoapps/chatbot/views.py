import json
import math
import logging
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from .models import ChatbotSession, ChatbotQuery
from .serializer import chatbot_query_list_serializer, chatbot_query_serializer, chatbot_session_list_serializer
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _
import requests
from .api import get_chatbot_bearer_token, get_chatbot_api_url

@require_http_methods('GET')
@login_required
def chatbot_fetch_query_list_view(request, session_id, skip, limit):
    user = request.user
    
    if session_id == '0':
        last_session = ChatbotSession.objects.filter(student=request.user).last()

        query_list = [] if last_session is None else last_session.chatbot_queries.order_by('-id').all()[skip:skip + limit]
        total = 0 if last_session is None else last_session.chatbot_queries.count()
        total_page = math.ceil(total/limit)
    else:
        query_list = ChatbotQuery.objects.filter(session__student=user, session__id=session_id).order_by('-id')[skip:skip + limit]
        total = ChatbotQuery.objects.filter(session__student=user, session__id=session_id).count()
        total_page = math.ceil(total / limit)

    remain_page = math.ceil((total - skip - limit)/limit)


    return JsonResponse(
        {
            'message': _('success'),
            'data': {
                'query_list': chatbot_query_list_serializer(query_list),
                'total_page': total_page,
                'remain_page': remain_page,
            }
        }, 
        status=200
    )

@require_http_methods('GET')
@login_required
def chatbot_fetch_session_list_view(request, skip, limit):
    user = request.user

    session_list = ChatbotSession.objects.filter(student=user).order_by('-id').all()[skip:skip + limit]
    total = ChatbotSession.objects.filter(student=user).count()
    total_page = math.ceil(total/limit)
    remain_page = math.ceil((total - skip - limit)/limit)

    return JsonResponse(
        {
            'message': _('success'),
            'data': {
                'session_list': chatbot_session_list_serializer(session_list),
                'total_page': total_page,
                'remain_page': remain_page,
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
    request_data = json.loads(request.body.decode('utf8'))

    query_msg = request_data.get('query_msg')
    session_id = request_data.get('session_id')

    session = ChatbotSession.objects.filter(id=session_id).last()

    if session is None: 
        session = ChatbotSession.objects.create(student=request.user)

    try:
        created_query = ChatbotQuery.objects.create(session=session, query_msg=query_msg)
    except Exception as e:
        logging.error(str(e))
        return JsonResponse(
            {
                'message': _('Internal Server Error'),
                'hash': request_data.get('hash')
            }, 
            status=500
        )

    response_msg = _chatbot_get_response(query_msg, session.id)
    if response_msg is None: 
        created_query.status = 'failed'
        created_query.save()
        return JsonResponse(
            {
                'message': _('Failed'),
                'data': chatbot_query_serializer(created_query),
                'hash': request_data.get('hash')
            }, 
            status=200
        )

    created_query.status = 'succeeded'
    created_query.response_msg = response_msg
    created_query.save()

    return JsonResponse(
        {
            'message': _('success'),
            'data': chatbot_query_serializer(created_query),
            'hash': request_data.get('hash')
        }, 
        status=200
    )

@require_http_methods('PUT')
@login_required
def chatbot_vote_response_view(request):
    data = json.loads(request.body.decode('utf8'))

    if data.get('vote') not in ['up', 'down', 'remove']:
        return JsonResponse(
            {
                'message': _('Vote must be "up" or "down" or "remove"')
            },
            status=200
        )
        
    response = ChatbotQuery.objects.filter(id=data.get('query_id')).first()
    if response is None: 
        return JsonResponse(
            {
                'message': _('Not found query response')
            },
            status=400
        )
    if data.get('vote') == 'remove': 
        response.vote = None
    else:
        response.vote = data.get('vote')

    response.save()

    return JsonResponse(
        {
            'message': _('success'),  
            'data': {
                'vote': data.get('vote'),
                'id': data.get('query_id')
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
        return JsonResponse(
            {
                'message': _('Not found query')
            },
            status=400
        )
    
    if query.status != 'failed':
        return JsonResponse(
            {
                'message': _('You can only retry on failed query')
            },
            status=400
        )
    
    response_msg = _chatbot_get_response(query.query_msg, query.session.id)

    if response_msg is None: 
        return JsonResponse(
            {
                'message': _('Internal Server Error'),
                'data': chatbot_query_serializer(query)
            },
            status=200
        )

    query.status = 'succeeded'
    query.response_msg = response_msg
    query.save()
    return JsonResponse(
        {
            'message': _('success'),
            'data': chatbot_query_serializer(query)
        },
        status=200
    )


@require_http_methods('PUT')
@login_required
def chatbot_cancel_query_view(request):
    data = json.loads(request.body.decode('utf8'))

    query = ChatbotQuery.objects.filter(id=data.get('query_id')).first()

    if query is None:
        return JsonResponse(
            {
                'message': _('Not found query')
            },
            status=400
        )
    
    if query.status != 'pending':
        return JsonResponse(
            {
                'message': _('This query has already finished')
            },
            status=400
        )

    query.status = 'canceled'
    return JsonResponse(
        {
            'message': _('success')
        },
        status=200
    )


# helper function
def _chatbot_get_response(query_msg, session_id):
    url = get_chatbot_api_url()
    headers = {
        'Content-Type': 'application/json', 
        'Authorization': f'Bearer {get_chatbot_bearer_token()}'
    }
    data = {
        'query': query_msg,
        'chat_id': session_id
    }

    r = requests.post(url, headers=headers, data=json.dumps(data))

    if r.status_code == 200:
        return r.json().get('data').get('response')

    else: 
        print('chatbot failed: ', r.status_code)
        try:
            print(r.json())
        except Exception as e: 
            print(str(e))
    
    return None