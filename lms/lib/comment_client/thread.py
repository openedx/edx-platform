from .utils import merge_dict, strip_blank, strip_none, extract, perform_request
from .utils import CommentClientError
import models
import settings


class Thread(models.Model):

    accessible_fields = [
        'id', 'title', 'body', 'anonymous', 'anonymous_to_peers', 'course_id',
        'closed', 'tags', 'votes', 'commentable_id', 'username', 'user_id',
        'created_at', 'updated_at', 'comments_count', 'unread_comments_count',
        'at_position_list', 'children', 'type', 'highlighted_title',
        'highlighted_body', 'endorsed', 'read', 'group_id', 'group_name', 'pinned', 'abuse_flaggers'
    ]

    updatable_fields = [
        'title', 'body', 'anonymous', 'anonymous_to_peers', 'course_id',
        'closed', 'tags', 'user_id', 'commentable_id', 'group_id', 'group_name', 'pinned'
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

        if query_params.get('text') or query_params.get('tags') or query_params.get('commentable_ids'):
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

    # TODO: This is currently overriding Model._retrieve only to add parameters
    # for the request. Model._retrieve should be modified to handle this such
    # that subclasses don't need to override for this.
    def _retrieve(self, *args, **kwargs):
        url = self.url(action='get', params=self.attributes)
        request_params = {
            'recursive': kwargs.get('recursive'),
            'user_id': kwargs.get('user_id'),
            'mark_as_read': kwargs.get('mark_as_read', True),
        }

        # user_id may be none, in which case it shouldn't be part of the
        # request.
        request_params = strip_none(request_params)

        response = perform_request('get', url, request_params)
        self.update_attributes(**response)

    def flagAbuse(self, user, voteable):
        if voteable.type == 'thread':
            url = _url_for_flag_abuse_thread(voteable.id)
        elif voteable.type == 'comment':
            url = _url_for_flag_comment(voteable.id)
        else:
            raise CommentClientError("Can only flag/unflag threads or comments")
        params = {'user_id': user.id}
        request = perform_request('put', url, params)
        voteable.update_attributes(request)

    def unFlagAbuse(self, user, voteable, removeAll):
        if voteable.type == 'thread':
            url = _url_for_unflag_abuse_thread(voteable.id)
        elif voteable.type == 'comment':
            url = _url_for_unflag_comment(voteable.id)
        else:
            raise CommentClientError("Can only flag/unflag for threads or comments")
        params = {'user_id': user.id}
        #if you're an admin, when you unflag, remove ALL flags
        if removeAll:
            params['all'] = True

        request = perform_request('put', url, params)
        voteable.update_attributes(request)

    def pin(self, user, thread_id):
        url = _url_for_pin_thread(thread_id)
        params = {'user_id': user.id}
        request = perform_request('put', url, params)
        self.update_attributes(request)

    def un_pin(self, user, thread_id):
        url = _url_for_un_pin_thread(thread_id)
        params = {'user_id': user.id}
        request = perform_request('put', url, params)
        self.update_attributes(request)


def _url_for_flag_abuse_thread(thread_id):
    return "{prefix}/threads/{thread_id}/abuse_flag".format(prefix=settings.PREFIX, thread_id=thread_id)


def _url_for_unflag_abuse_thread(thread_id):
    return "{prefix}/threads/{thread_id}/abuse_unflag".format(prefix=settings.PREFIX, thread_id=thread_id)


def _url_for_pin_thread(thread_id):
    return "{prefix}/threads/{thread_id}/pin".format(prefix=settings.PREFIX, thread_id=thread_id)


def _url_for_un_pin_thread(thread_id):
    return "{prefix}/threads/{thread_id}/unpin".format(prefix=settings.PREFIX, thread_id=thread_id)
