# pylint: disable=missing-docstring,unused-argument


import logging

from .utils import CommentClientRequestError, extract, perform_request, get_course_key
from forum import api as forum_api
from lms.djangoapps.discussion.toggles import is_forum_v2_enabled

log = logging.getLogger(__name__)


class Model:

    accessible_fields = ['id']
    updatable_fields = ['id']
    initializable_fields = ['id']
    base_url = None
    default_retrieve_params = {}
    metric_tag_fields = []

    DEFAULT_ACTIONS_WITH_ID = ['get', 'put', 'delete']
    DEFAULT_ACTIONS_WITHOUT_ID = ['get_all', 'post']
    DEFAULT_ACTIONS = DEFAULT_ACTIONS_WITH_ID + DEFAULT_ACTIONS_WITHOUT_ID

    def __init__(self, *args, **kwargs):
        self.attributes = extract(kwargs, self.accessible_fields)
        self.retrieved = False

    def __getattr__(self, name):
        if name == 'id':
            return self.attributes.get('id', None)
        try:
            return self.attributes[name]
        except KeyError:
            if self.retrieved or self.id is None:
                raise AttributeError(f"Field {name} does not exist")  # lint-amnesty, pylint: disable=raise-missing-from
            self.retrieve()
            return self.__getattr__(name)

    def __setattr__(self, name, value):
        if name == 'attributes' or name not in self.accessible_fields + self.updatable_fields:
            super().__setattr__(name, value)
        else:
            self.attributes[name] = value

    def __getitem__(self, key):
        if key not in self.accessible_fields:
            raise KeyError(f"Field {key} does not exist")
        return self.attributes.get(key)

    def __setitem__(self, key, value):
        if key not in self.accessible_fields + self.updatable_fields:
            raise KeyError(f"Field {key} does not exist")
        self.attributes.__setitem__(key, value)

    def items(self, *args, **kwargs):
        return self.attributes.items(*args, **kwargs)

    def get(self, *args, **kwargs):
        return self.attributes.get(*args, **kwargs)

    def to_dict(self):
        self.retrieve()
        return self.attributes

    def retrieve(self, *args, **kwargs):
        if not self.retrieved:
            self._retrieve(*args, **kwargs)
            self.retrieved = True
        return self

    def _retrieve(self, *args, **kwargs):
        course_id = self.attributes.get("course_id") or kwargs.get("course_id")
        if not course_id:
            course_id = forum_api.get_course_id_by_comment(self.id)
        course_key = get_course_key(course_id)
        response = None
        if is_forum_v2_enabled(course_key):
            if self.type == "comment":
                response = forum_api.get_parent_comment(comment_id=self.attributes["id"], course_id=str(course_key))
            if response is None:
                raise CommentClientRequestError("Forum v2 API call is missing")
        else:
            url = self.url(action='get', params=self.attributes)
            response = perform_request(
                'get',
                url,
                self.default_retrieve_params,
                metric_tags=self._metric_tags,
                metric_action='model.retrieve'
            )
        self._update_from_response(response)

    @property
    def _metric_tags(self):
        """
        Returns a list of tags to be used when recording metrics about this model.

        Each field named in ``self.metric_tag_fields`` is used as a tag value,
        under the key ``<class>.<metric_field>``. The tag model_class is used to
        record the class name of the model.
        """
        tags = [
            f'{self.__class__.__name__}.{attr}:{self[attr]}'
            for attr in self.metric_tag_fields
            if attr in self.attributes
        ]
        tags.append(f'model_class:{self.__class__.__name__}')
        return tags

    @classmethod
    def find(cls, id):  # pylint: disable=redefined-builtin
        return cls(id=id)

    @classmethod
    def retrieve_all(cls, params=None):
        """
        Performs a GET request against the resource's listing endpoint.

        Arguments:
            params: A dictionary of parameters to be passed as the request's query string.

        Returns:
            The parsed JSON response from the backend.
        """
        return perform_request(
            'get',
            cls.url(action='get_all'),
            params,
            metric_tags=[f'model_class:{cls.__name__}'],
            metric_action='model.retrieve_all',
        )

    def _update_from_response(self, response_data):
        for k, v in response_data.items():
            if k in self.accessible_fields:
                setattr(self, k, v)
            else:
                log.warning(
                    "Unexpected field {field_name} in model {model_name}".format(
                        field_name=k,
                        model_name=self.__class__.__name__
                    )
                )

    def updatable_attributes(self):
        return extract(self.attributes, self.updatable_fields)

    def initializable_attributes(self):
        return extract(self.attributes, self.initializable_fields)

    @classmethod
    def before_save(cls, instance):
        pass

    @classmethod
    def after_save(cls, instance):
        pass

    def save(self, params=None):
        """
        Invokes Forum's POST/PUT service to create/update thread
        """
        self.before_save(self)
        if self.id:   # if we have id already, treat this as an update
            response = self.handle_update(params)
        else:  # otherwise, treat this as an insert
            response = self.handle_create(params)

        self.retrieved = True
        self._update_from_response(response)
        self.after_save(self)

    def delete(self):
        course_key = get_course_key(self.attributes.get("course_id"))
        if is_forum_v2_enabled(course_key):
            response = None
            if self.type == "comment":
                response = forum_api.delete_comment(comment_id=self.attributes["id"], course_id=str(course_key))
            elif self.type == "thread":
                response = forum_api.delete_thread(thread_id=self.attributes["id"], course_id=str(course_key))
            if response is None:
                raise CommentClientRequestError("Forum v2 API call is missing")
        else:
            url = self.url(action='delete', params=self.attributes)
            response = perform_request('delete', url, metric_tags=self._metric_tags, metric_action='model.delete')
        self.retrieved = True
        self._update_from_response(response)

    @classmethod
    def url_with_id(cls, params=None):
        if params is None:
            params = {}
        return cls.base_url + '/' + str(params['id'])

    @classmethod
    def url_without_id(cls, params=None):
        return cls.base_url

    @classmethod
    def url(cls, action, params=None):
        if params is None:
            params = {}
        if cls.base_url is None:
            raise CommentClientRequestError("Must provide base_url when using default url function")
        if action not in cls.DEFAULT_ACTIONS:  # lint-amnesty, pylint: disable=no-else-raise
            raise ValueError(
                f"Invalid action {action}. The supported action must be in {str(cls.DEFAULT_ACTIONS)}"
            )
        elif action in cls.DEFAULT_ACTIONS_WITH_ID:
            try:
                return cls.url_with_id(params)
            except KeyError:
                raise CommentClientRequestError(f"Cannot perform action {action} without id")  # lint-amnesty, pylint: disable=raise-missing-from
        else:   # action must be in DEFAULT_ACTIONS_WITHOUT_ID now
            return cls.url_without_id()

    def handle_update(self, params=None):
        request_params = self.updatable_attributes()
        if params:
            request_params.update(params)
        course_id = self.attributes.get("course_id") or request_params.get("course_id")
        course_key = get_course_key(course_id)
        if is_forum_v2_enabled(course_key):
            response = None
            if self.type == "comment":
                response = self.handle_update_comment(request_params, str(course_key))
            elif self.type == "thread":
                response = self.handle_update_thread(request_params, str(course_key))
            elif self.type == "user":
                response = self.handle_update_user(request_params, str(course_key))
            if response is None:
                raise CommentClientRequestError("Forum v2 API call is missing")
        else:
            response = self.perform_http_put_request(request_params)
        return response

    def handle_update_user(self, request_params, course_id):
        try:
            username = request_params["username"]
            external_id = str(request_params["external_id"])
        except KeyError as e:
            raise e
        response = forum_api.update_user(
            external_id,
            username,
            course_id,
        )
        return response

    def handle_update_comment(self, request_params, course_id):
        request_data = {
            "comment_id": self.attributes["id"],
            "body": request_params.get("body"),
            "course_id": request_params.get("course_id"),
            "user_id": request_params.get("user_id"),
            "anonymous": request_params.get("anonymous"),
            "anonymous_to_peers": request_params.get("anonymous_to_peers"),
            "endorsed": request_params.get("endorsed"),
            "closed": request_params.get("closed"),
            "editing_user_id": request_params.get("editing_user_id"),
            "edit_reason_code": request_params.get("edit_reason_code"),
            "endorsement_user_id": request_params.get("endorsement_user_id"),
            "course_key": course_id
        }
        request_data = {k: v for k, v in request_data.items() if v is not None}
        response = forum_api.update_comment(**request_data)
        return response

    def handle_update_thread(self, request_params, course_id):
        request_data = {
            "thread_id": self.attributes["id"],
            "title": request_params.get("title"),
            "body": request_params.get("body"),
            "course_id": request_params.get("course_id"),
            "anonymous": request_params.get("anonymous"),
            "anonymous_to_peers": request_params.get("anonymous_to_peers"),
            "closed": request_params.get("closed"),
            "commentable_id": request_params.get("commentable_id"),
            "user_id": request_params.get("user_id"),
            "editing_user_id": request_params.get("editing_user_id"),
            "pinned": request_params.get("pinned"),
            "thread_type": request_params.get("thread_type"),
            "edit_reason_code": request_params.get("edit_reason_code"),
            "close_reason_code": request_params.get("close_reason_code"),
            "closing_user_id": request_params.get("closing_user_id"),
            "endorsed": request_params.get("endorsed"),
            "course_key": course_id
        }
        request_data = {k: v for k, v in request_data.items() if v is not None}
        response = forum_api.update_thread(**request_data)
        return response

    def perform_http_put_request(self, request_params):
        url = self.url(action="put", params=self.attributes)
        response = perform_request(
            "put",
            url,
            request_params,
            metric_tags=self._metric_tags,
            metric_action="model.update",
        )
        return response

    def perform_http_post_request(self):
        url = self.url(action="post", params=self.attributes)
        response = perform_request(
            "post",
            url,
            self.initializable_attributes(),
            metric_tags=self._metric_tags,
            metric_action="model.insert",
        )
        return response

    def handle_create(self, params=None):
        course_id = self.attributes.get("course_id") or params.get("course_id")
        course_key = get_course_key(course_id)
        if is_forum_v2_enabled(course_key):
            response = None
            if self.type == "comment":
                response = self.handle_create_comment(str(course_key))
            elif self.type == "thread":
                response = self.handle_create_thread(str(course_key))
            if response is None:
                raise CommentClientRequestError("Forum v2 API call is missing")
        else:
            response = self.perform_http_post_request()
        return response

    def handle_create_comment(self, course_id):
        request_data = self.initializable_attributes()
        body = request_data["body"]
        user_id = request_data["user_id"]
        course_id = course_id or str(request_data["course_id"])
        if parent_id := self.attributes.get("parent_id"):
            response = forum_api.create_child_comment(
                parent_id,
                body,
                user_id,
                course_id,
                request_data.get("anonymous", False),
                request_data.get("anonymous_to_peers", False),
            )
        else:
            response = forum_api.create_parent_comment(
                self.attributes["thread_id"],
                body,
                user_id,
                course_id,
                request_data.get("anonymous", False),
                request_data.get("anonymous_to_peers", False),
            )
        return response

    def handle_create_thread(self, course_id):
        request_data = self.initializable_attributes()
        response = forum_api.create_thread(
            title=request_data["title"],
            body=request_data["body"],
            course_id=course_id or str(request_data["course_id"]),
            user_id=str(request_data["user_id"]),
            anonymous=request_data.get("anonymous", False),
            anonymous_to_peers=request_data.get("anonymous_to_peers", False),
            commentable_id=request_data.get("commentable_id", "course"),
            thread_type=request_data.get("thread_type", "discussion"),
            group_id=request_data.get("group_id", None),
            context=request_data.get("context", None),
        )
        return response
