def chatbot_query_serializer(query):
    return {
        'id': query.id,
        'session_id': query.session.id,
        'student_id': query.session.student.id,
        'query_msg': query.query_msg,
        'response_msg': query.response_msg,
        'status': query.status,
        'vote': query.vote,
    }

def chatbot_query_list_serializer(query_list):
    result = []
    for query in query_list: 
        result.append(chatbot_query_serializer(query))
    return result


def chatbot_session_list_serializer(session_list):
    result = []
    for session in session_list: 
        query_list = []
        for query in session.chatbot_queries.all():
            query_list.append(chatbot_query_serializer(query))
        result.append(query_list)
    
    return result