from utils import *

import models
import settings

class Thread(models.Model):

    accessible_fields = [
        'id', 'title', 'body', 'anonymous',
        'course_id', 'closed', 'tags', 'votes',
        'commentable_id', 'username', 'user_id',
        'created_at', 'updated_at', 'comments_count',
        'at_position_list', 'children', 'type',
        'highlighted_title', 'highlighted_body',
        'endorsed'
    ]

    updatable_fields = [
        'title', 'body', 'anonymous', 'course_id', 
        'closed', 'tags', 'user_id', 'commentable_id',
    ]

    initializable_fields = updatable_fields

    base_url = "{prefix}/threads".format(prefix=settings.PREFIX)
    default_retrieve_params = {'recursive': False}
    type = 'thread'

    @classmethod
    def search(cls, query_params, *args, **kwargs):
        default_params = {'page': 1,
                          'per_page': 20,
                          'course_id': query_params['course_id'],
                          'recursive': False}
        params = merge_dict(default_params, strip_blank(strip_none(query_params)))
        if query_params.get('text') or query_params.get('tags'):
            url = cls.url(action='search')
        else:
            url = cls.url(action='get_all', params=extract(params, 'commentable_id'))
            if params.get('commentable_id'):
                del params['commentable_id']
        response = perform_request('get', url, params, *args, **kwargs)
        return response.get('collection', []), response.get('page', 1), response.get('num_pages', 1)
        
    @classmethod
    def url_for_threads(cls, params={}):
        if params.get('commentable_id'):
            return "{prefix}/{commentable_id}/threads".format(prefix=settings.PREFIX, commentable_id=params['commentable_id'])
        else:
            return "{prefix}/threads".format(prefix=settings.PREFIX)

    @classmethod
    def url_for_search_threads(cls, params={}):
        return "{prefix}/search/threads".format(prefix=settings.PREFIX)

    @classmethod
    def url(cls, action, params={}):
        if action in ['get_all', 'post']:
            return cls.url_for_threads(params)
        elif action == 'search':
            return cls.url_for_search_threads(params)
        else:
            return super(Thread, cls).url(action, params)

    def _retrieve(self, *args, **kwargs):
        url = self.url(action='get', params=self.attributes)
        response = perform_request('get', url, {'recursive': kwargs.get('recursive')})
        self.update_attributes(**response)
