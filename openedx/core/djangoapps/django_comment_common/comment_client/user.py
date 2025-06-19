# pylint: disable=missing-docstring,protected-access
""" User model wrapper for comment service"""

from . import models, settings, utils
from forum import api as forum_api
from forum.utils import ForumV2RequestError, str_to_bool
from openedx.core.djangoapps.discussions.config.waffle import is_forum_v2_enabled


class User(models.Model):

    accessible_fields = [
        'username', 'follower_ids', 'upvoted_ids', 'downvoted_ids',
        'id', 'external_id', 'subscribed_user_ids', 'children', 'course_id',
        'group_id', 'subscribed_thread_ids', 'subscribed_commentable_ids',
        'subscribed_course_ids', 'threads_count', 'comments_count',
        'default_sort_key'
    ]

    updatable_fields = ['username', 'external_id', 'default_sort_key']
    initializable_fields = updatable_fields

    metric_tag_fields = ['course_id']

    base_url = f"{settings.PREFIX}/users"
    default_retrieve_params = {'complete': True}
    type = 'user'

    @classmethod
    def from_django_user(cls, user):
        return cls(id=str(user.id),
                   external_id=str(user.id),
                   username=user.username)

    def read(self, source):
        """
        Calls cs_comments_service to mark thread as read for the user
        """
        course_id = self.attributes.get("course_id")
        course_key = utils.get_course_key(course_id)
        if is_forum_v2_enabled(course_key):
            forum_api.mark_thread_as_read(self.id, source.id, course_id=str(course_id))
        else:
            params = {'source_type': source.type, 'source_id': source.id}
            utils.perform_request(
                'post',
                _url_for_read(self.id),
                params,
                metric_action='user.read',
                metric_tags=self._metric_tags + [f'target.type:{source.type}'],
            )

    def follow(self, source, course_id=None):
        course_key = utils.get_course_key(self.attributes.get("course_id") or course_id)
        if is_forum_v2_enabled(course_key):
            forum_api.create_subscription(
                user_id=self.id,
                source_id=source.id,
                course_id=str(course_key)
            )
        else:
            params = {'source_type': source.type, 'source_id': source.id}
            utils.perform_request(
                'post',
                _url_for_subscription(self.id),
                params,
                metric_action='user.follow',
                metric_tags=self._metric_tags + [f'target.type:{source.type}'],
            )

    def unfollow(self, source, course_id=None):
        course_key = utils.get_course_key(self.attributes.get("course_id") or course_id)
        if is_forum_v2_enabled(course_key):
            forum_api.delete_subscription(
                user_id=self.id,
                source_id=source.id,
                course_id=str(course_key)
            )
        else:
            params = {'source_type': source.type, 'source_id': source.id}
            utils.perform_request(
                'delete',
                _url_for_subscription(self.id),
                params,
                metric_action='user.unfollow',
                metric_tags=self._metric_tags + [f'target.type:{source.type}'],
            )

    def vote(self, voteable, value, course_id=None):
        course_key = utils.get_course_key(self.attributes.get("course_id") or course_id)
        if voteable.type == 'thread':
            response = forum_api.update_thread_votes(
                thread_id=voteable.id,
                user_id=self.id,
                value=value,
                course_id=str(course_key)
            )
        elif voteable.type == 'comment':
            response = forum_api.update_comment_votes(
                comment_id=voteable.id,
                user_id=self.id,
                value=value,
                course_id=str(course_key)
            )
        else:
            raise utils.CommentClientRequestError("Can only vote / unvote for threads or comments")
        voteable._update_from_response(response)

    def unvote(self, voteable, course_id=None):
        course_key = utils.get_course_key(self.attributes.get("course_id") or course_id)
        if voteable.type == 'thread':
            response = forum_api.delete_thread_vote(
                thread_id=voteable.id,
                user_id=self.id,
                course_id=str(course_key)
            )
        elif voteable.type == 'comment':
            response = forum_api.delete_comment_vote(
                comment_id=voteable.id,
                user_id=self.id,
                course_id=str(course_key)
            )
        else:
            raise utils.CommentClientRequestError("Can only vote / unvote for threads or comments")

        voteable._update_from_response(response)

    def active_threads(self, query_params=None):
        if query_params is None:
            query_params = {}
        if not self.course_id:
            raise utils.CommentClientRequestError("Must provide course_id when retrieving active threads for the user")
        url = _url_for_user_active_threads(self.id)
        params = {'course_id': str(self.course_id)}
        params.update(query_params)
        course_key = utils.get_course_key(self.attributes.get("course_id"))
        if is_forum_v2_enabled(course_key):
            if user_id := params.get("user_id"):
                params["user_id"] = str(user_id)
            if page := params.get("page"):
                params["page"] = int(page)
            if per_page := params.get("per_page"):
                params["per_page"] = int(per_page)
            if count_flagged := params.get("count_flagged", False):
                params["count_flagged"] = str_to_bool(count_flagged)
            if not params.get("course_id"):
                params["course_id"] = str(course_key)
            response = forum_api.get_user_active_threads(**params)
        else:
            response = utils.perform_request(
                'get',
                url,
                params,
                metric_action='user.active_threads',
                metric_tags=self._metric_tags,
                paged_results=True,
            )
        return response.get('collection', []), response.get('page', 1), response.get('num_pages', 1)

    def subscribed_threads(self, query_params=None):
        if query_params is None:
            query_params = {}
        if not self.course_id:
            raise utils.CommentClientRequestError(
                "Must provide course_id when retrieving subscribed threads for the user",
            )
        url = _url_for_user_subscribed_threads(self.id)
        params = {'course_id': str(self.course_id)}
        params.update(query_params)
        course_key = utils.get_course_key(self.attributes.get("course_id"))
        if is_forum_v2_enabled(course_key):
            if page := params.get("page"):
                params["page"] = int(page)
            if per_page := params.get("per_page"):
                params["per_page"] = int(per_page)
            if count_flagged := params.get("count_flagged", False):
                params["count_flagged"] = str_to_bool(count_flagged)
            if not params.get("course_id"):
                params["course_id"] = str(course_key)

            user_id = params.pop("user_id", None)
            if "text" in params:
                params.pop("text")
            response = forum_api.get_user_subscriptions(user_id, str(course_key), params)
        else:
            response = utils.perform_request(
                'get',
                url,
                params,
                metric_action='user.subscribed_threads',
                metric_tags=self._metric_tags,
                paged_results=True
            )
        return utils.CommentClientPaginatedResult(
            collection=response.get('collection', []),
            page=response.get('page', 1),
            num_pages=response.get('num_pages', 1),
            thread_count=response.get('thread_count', 0)
        )

    def _retrieve(self, *args, **kwargs):
        url = self.url(action='get', params=self.attributes)
        retrieve_params = self.default_retrieve_params.copy()
        retrieve_params.update(kwargs)

        if self.attributes.get('course_id'):
            retrieve_params['course_id'] = str(self.course_id)
        if self.attributes.get('group_id'):
            retrieve_params['group_id'] = self.group_id

        # course key -> id conversation
        course_id = retrieve_params.get('course_id')
        if course_id:
            course_id = str(course_id)
            retrieve_params['course_id'] = course_id
        course_key = utils.get_course_key(course_id)

        if is_forum_v2_enabled(course_key):
            group_ids = [retrieve_params['group_id']] if 'group_id' in retrieve_params else []
            is_complete = retrieve_params['complete']
            try:
                response = forum_api.get_user(
                    self.attributes["id"],
                    group_ids=group_ids,
                    course_id=course_id,
                    complete=is_complete
                )
            except ForumV2RequestError as e:
                self.save({"course_id": course_id})
                response = forum_api.get_user(
                    self.attributes["id"],
                    group_ids=group_ids,
                    course_id=course_id,
                    complete=is_complete
                )
        else:
            try:
                response = utils.perform_request(
                    'get',
                    url,
                    retrieve_params,
                    metric_action='model.retrieve',
                    metric_tags=self._metric_tags,
                )
            except utils.CommentClientRequestError as e:
                if e.status_code == 404:
                    # attempt to gracefully recover from a previous failure
                    # to sync this user to the comments service.
                    self.save()
                    response = utils.perform_request(
                        'get',
                        url,
                        retrieve_params,
                        metric_action='model.retrieve',
                        metric_tags=self._metric_tags,
                    )
                else:
                    raise
        self._update_from_response(response)

    def retire(self, retired_username):
        course_key = utils.get_course_key(self.attributes.get("course_id"))
        if is_forum_v2_enabled(course_key):
            forum_api.retire_user(user_id=self.id, retired_username=retired_username, course_id=str(course_key))
        else:
            url = _url_for_retire(self.id)
            params = {'retired_username': retired_username}
            utils.perform_request(
                'post',
                url,
                params,
                raw=True,
                metric_action='user.retire',
                metric_tags=self._metric_tags
            )

    def replace_username(self, new_username):
        course_key = utils.get_course_key(self.attributes.get("course_id"))
        if is_forum_v2_enabled(course_key):
            forum_api.update_username(user_id=self.id, new_username=new_username, course_id=str(course_key))
        else:
            url = _url_for_username_replacement(self.id)
            params = {"new_username": new_username}

            utils.perform_request(
                'post',
                url,
                params,
                raw=True,
            )


def _url_for_vote_comment(comment_id):
    return f"{settings.PREFIX}/comments/{comment_id}/votes"


def _url_for_vote_thread(thread_id):
    return f"{settings.PREFIX}/threads/{thread_id}/votes"


def _url_for_subscription(user_id):
    return f"{settings.PREFIX}/users/{user_id}/subscriptions"


def _url_for_user_active_threads(user_id):
    return f"{settings.PREFIX}/users/{user_id}/active_threads"


def _url_for_user_subscribed_threads(user_id):
    return f"{settings.PREFIX}/users/{user_id}/subscribed_threads"


def _url_for_read(user_id):
    """
    Returns cs_comments_service url endpoint to mark thread as read for given user_id
    """
    return f"{settings.PREFIX}/users/{user_id}/read"


def _url_for_retire(user_id):
    """
    Returns cs_comments_service url endpoint to retire a user (remove all post content, etc.)
    """
    return f"{settings.PREFIX}/users/{user_id}/retire"


def _url_for_username_replacement(user_id):
    """
    Returns cs_comments_servuce url endpoint to replace the username of a user
    """
    return f"{settings.PREFIX}/users/{user_id}/replace_username"
