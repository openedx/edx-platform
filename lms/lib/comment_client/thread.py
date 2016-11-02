import logging

from eventtracking import tracker
from .utils import merge_dict, strip_blank, strip_none, extract, perform_request, CommentClientPaginatedResult
from .utils import CommentClientRequestError
import models
import settings

log = logging.getLogger(__name__)


class Thread(models.Model):

    # accessible_fields can be set and retrieved on the model
    accessible_fields = [
        'id', 'title', 'body', 'anonymous', 'anonymous_to_peers', 'course_id',
        'closed', 'tags', 'votes', 'commentable_id', 'username', 'user_id',
        'created_at', 'updated_at', 'comments_count', 'unread_comments_count',
        'at_position_list', 'children', 'type', 'highlighted_title',
        'highlighted_body', 'endorsed', 'read', 'group_id', 'group_name', 'pinned',
        'abuse_flaggers', 'resp_skip', 'resp_limit', 'resp_total', 'thread_type',
        'endorsed_responses', 'non_endorsed_responses', 'non_endorsed_resp_total',
        'context', 'last_activity_at',
    ]

    # updateable_fields are sent in PUT requests
    updatable_fields = [
        'title', 'body', 'anonymous', 'anonymous_to_peers', 'course_id', 'read',
        'closed', 'user_id', 'commentable_id', 'group_id', 'group_name', 'pinned', 'thread_type'
    ]

    # metric_tag_fields are used by Datadog to record metrics about the model
    metric_tag_fields = [
        'course_id', 'group_id', 'pinned', 'closed', 'anonymous', 'anonymous_to_peers',
        'endorsed', 'read'
    ]

    # initializable_fields are sent in POST requests
    initializable_fields = updatable_fields + ['thread_type', 'context']

    base_url = "{prefix}/threads".format(prefix=settings.PREFIX)
    default_retrieve_params = {'recursive': False}
    type = 'thread'

    @classmethod
    def search(cls, query_params):

        # NOTE: Params 'recursive' and 'with_responses' are currently not used by
        # either the 'search' or 'get_all' actions below.  Both already use
        # with_responses=False internally in the comment service, so no additional
        # optimization is required.
        default_params = {'page': 1,
                          'per_page': 20,
                          'course_id': query_params['course_id']}
        params = merge_dict(default_params, strip_blank(strip_none(query_params)))

        if query_params.get('text'):
            url = cls.url(action='search')
        else:
            url = cls.url(action='get_all', params=extract(params, 'commentable_id'))
            if params.get('commentable_id'):
                del params['commentable_id']
        response = perform_request(
            'get',
            url,
            params,
            metric_tags=[u'course_id:{}'.format(query_params['course_id'])],
            metric_action='thread.search',
            paged_results=True
        )
        if query_params.get('text'):
            search_query = query_params['text']
            course_id = query_params['course_id']
            group_id = query_params['group_id'] if 'group_id' in query_params else None
            requested_page = params['page']
            total_results = response.get('total_results')
            corrected_text = response.get('corrected_text')
            # Record search result metric to allow search quality analysis.
            # course_id is already included in the context for the event tracker
            tracker.emit(
                'edx.forum.searched',
                {
                    'query': search_query,
                    'corrected_text': corrected_text,
                    'group_id': group_id,
                    'page': requested_page,
                    'total_results': total_results,
                }
            )
            log.info(
                u'forum_text_search query="{search_query}" corrected_text="{corrected_text}" course_id={course_id} group_id={group_id} page={requested_page} total_results={total_results}'.format(
                    search_query=search_query,
                    corrected_text=corrected_text,
                    course_id=course_id,
                    group_id=group_id,
                    requested_page=requested_page,
                    total_results=total_results
                )
            )

        return CommentClientPaginatedResult(
            collection=response.get('collection', []),
            page=response.get('page', 1),
            num_pages=response.get('num_pages', 1),
            thread_count=response.get('thread_count', 0),
            corrected_text=response.get('corrected_text', None)
        )

    @classmethod
    def url_for_threads(cls, params={}):
        if params.get('commentable_id'):
            return u"{prefix}/{commentable_id}/threads".format(prefix=settings.PREFIX, commentable_id=params['commentable_id'])
        else:
            return u"{prefix}/threads".format(prefix=settings.PREFIX)

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
            'with_responses': kwargs.get('with_responses', False),
            'user_id': kwargs.get('user_id'),
            'mark_as_read': kwargs.get('mark_as_read', True),
            'resp_skip': kwargs.get('response_skip'),
            'resp_limit': kwargs.get('response_limit'),
        }
        request_params = strip_none(request_params)

        response = perform_request(
            'get',
            url,
            request_params,
            metric_action='model.retrieve',
            metric_tags=self._metric_tags
        )
        self._update_from_response(response)

    def flagAbuse(self, user, voteable):
        if voteable.type == 'thread':
            url = _url_for_flag_abuse_thread(voteable.id)
        elif voteable.type == 'comment':
            url = _url_for_flag_comment(voteable.id)
        else:
            raise CommentClientRequestError("Can only flag/unflag threads or comments")
        params = {'user_id': user.id}
        response = perform_request(
            'put',
            url,
            params,
            metric_action='thread.abuse.flagged',
            metric_tags=self._metric_tags
        )
        voteable._update_from_response(response)

    def unFlagAbuse(self, user, voteable, removeAll):
        if voteable.type == 'thread':
            url = _url_for_unflag_abuse_thread(voteable.id)
        elif voteable.type == 'comment':
            url = _url_for_unflag_comment(voteable.id)
        else:
            raise CommentClientRequestError("Can only flag/unflag for threads or comments")
        params = {'user_id': user.id}
        #if you're an admin, when you unflag, remove ALL flags
        if removeAll:
            params['all'] = True

        response = perform_request(
            'put',
            url,
            params,
            metric_tags=self._metric_tags,
            metric_action='thread.abuse.unflagged'
        )
        voteable._update_from_response(response)

    def pin(self, user, thread_id):
        url = _url_for_pin_thread(thread_id)
        params = {'user_id': user.id}
        response = perform_request(
            'put',
            url,
            params,
            metric_tags=self._metric_tags,
            metric_action='thread.pin'
        )
        self._update_from_response(response)

    def un_pin(self, user, thread_id):
        url = _url_for_un_pin_thread(thread_id)
        params = {'user_id': user.id}
        response = perform_request(
            'put',
            url,
            params,
            metric_tags=self._metric_tags,
            metric_action='thread.unpin'
        )
        self._update_from_response(response)


def _url_for_flag_abuse_thread(thread_id):
    return "{prefix}/threads/{thread_id}/abuse_flag".format(prefix=settings.PREFIX, thread_id=thread_id)


def _url_for_unflag_abuse_thread(thread_id):
    return "{prefix}/threads/{thread_id}/abuse_unflag".format(prefix=settings.PREFIX, thread_id=thread_id)


def _url_for_pin_thread(thread_id):
    return "{prefix}/threads/{thread_id}/pin".format(prefix=settings.PREFIX, thread_id=thread_id)


def _url_for_un_pin_thread(thread_id):
    return "{prefix}/threads/{thread_id}/unpin".format(prefix=settings.PREFIX, thread_id=thread_id)
