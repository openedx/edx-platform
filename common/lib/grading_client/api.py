#from django.conf import settings

import requests
import slumber
import simplejson as json
from django.core.serializers.json import DjangoJSONEncoder

# HOST = getattr(settings, 'GRADING_SERVICE_HOST', 'http://localhost:3000/')
# The client library *should* be django independent. Django client should override this value somehow.
HOST= 'http://localhost:3000/'
API = slumber.API(HOST)


class APIModel(object):
    """
    A base class for making classes interact easily with a web API.
    """
    # This is kind of a premature optimization, but it restricts objects to only have fields specified explicitly. Saves
    # a lot of memory because the object doesn't need to have a dict, and I think that might be an issue with some pages
    __slots__ = ['_id', 'errors']
    __attributes__ = []
    __base_url__ = ""
    __parent__ = None
    def __init__(self, **kwargs):
        self.update_attributes(**kwargs)

    def get_parents(self):
        p = self.__parent__
        parents = []
        while p:
            parents.append(p)
            p = p.__parent__
        parents.reverse()
        return parents

    def url(self):
        # I think the smart thing to do is to ask your parent for its base URL
        if self.id:
            return slumber.url_join(self.__base_url__, self.id)
        else:
            return self.__base_url__

    def update_attributes(self, **kwargs):
        if 'id' in kwargs and kwargs['id'] is not None:
            self._id = int(kwargs['id'])
        for attribute in self.__attributes__:
            if attribute in kwargs:
                setattr(self, attribute, kwargs[attribute])

    def to_json(self):
        attributes = dict([(key, getattr(self,key, None)) for key in self.__attributes__ if hasattr(self, key)])
        return json.dumps({self.json_root:attributes}, cls=DjangoJSONEncoder)

    def save(self):
        # TODO: Think of a better way to handle nested resources, currently you have to manually set __base_url__
        params = self.to_json()
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        post_url = slumber.url_join(HOST, self.url())
        if self.id: # This object was retrieved from the service or otherwise persisted
            response = requests.put(post_url, data=params, headers=headers)
        else:
            response = requests.post(post_url, data=params, headers=headers)
        if response.status_code == 200:
            self.update_attributes(**response.json)
        else:
            # TODO: handle errors
            print response
            print response.text
            if response.status_code == 404:
                raise Exception("404 Not Found")
            if response.json:
                self.errors = response.json['errors']
            print self.errors
        return self

    def delete(self):
        url = slumber.url_join(HOST, self.url())
        if self.id:
            response = requests.delete(url)
            if response.status_code == 200:
                self._id = None

    @property
    def json_root(self):
      return self.__class__.__name__.lower()

    @property
    def id(self):
        """
        Returns the object's primary key, or None if it hasn't been persisted
        """
        try:
            return self._id
        except AttributeError:
            return None

class User(APIModel):
    __attributes__ = ['name', 'external_id']
    __slots__ = ['name', 'external_id', 'tasks']
    __base_url__ = 'users'

    def __init__(self, **kwargs):
        self.update_attributes(**kwargs)
        self.tasks = []
    @staticmethod
    def get_by_id(id):
        return User(**API.users(id).get())
    @staticmethod
    def get_by_external_id(id):
        return User(**API.users.get_by_external_id(id).get())
#    def submissions(self):
#        API.users(self.id).submissions.get()

class Question(APIModel):
    __attributes__ = ['external_id', 'rubric_id', 'total_points']
    __slots__ = __attributes__ + ['_grading_configuration']
    __base_url__ = 'questions'
    def submissions(self):
        return [Submission(**data) for data in API.questions(id).submissions.get()]

    @property
    def grading_queue(self):
        return GradingQueue(self)

    @property
    def grading_configuration(self):
        if not hasattr(self, '_grading_configuration'):
            # Try to query the service for the grading configuration
            response = requests.get(slumber.url_join(HOST, 'questions', self.id, 'grading_configuration'))
            if response.status_code == 200:
                self._grading_configuration = GradingConfiguration(**response.json)
            else:
                self._grading_configuration = GradingConfiguration(question_id=self.id)
        return self._grading_configuration

    @staticmethod
    def get_by_id(id):
        return Question(API.questions(id).get())

class Submission(APIModel):
    __attributes__ = ['question_id', 'user_id', 'external_id']
    __slots__ = __attributes__
    __base_url__ = 'submissions'
    def evaluations(self, start=None, end=None):
        # TODO: Support pagination
        evaluations_url = slumber.url_join(self.url(), 'evaluations')
        response = requests.get(evaluations_url)
        if response.status_code == 200:
            self.evaluations = [Evaluation(**data) for data in response.json]

    def url(self):
        if self.id:
            return slumber.url_join('questions', self.question_id, 'submissions', self.id)
        else:
            return slumber.url_join('questions', self.question_id, 'submissions')

    @staticmethod
    def get_by_question_id_and_id(question_id, _id):
        return Submission(**API.questions(question_id).submissions(_id).get())

    @staticmethod
    def get_by_id(_id):
        return Submission(**API.submissions(_id).get())

class Rubric(APIModel):
    __attributes__ = ['rubric_type', 'title', 'total_points', 'published']
    __slots__ = ['rubric_type', 'title', 'total_points', 'published', 'entries']
    __base_url__ = 'rubrics'
    def __init__(self, **kwargs):
        entries = kwargs.pop('entries', None)
        self.update_attributes(**kwargs)
        if entries:
            self.entries = [RubricEntry(data) for data in entries]
        else:
            self.entries = []
    @staticmethod
    def get_by_id(id):
        return Rubric(API.rubrics(id).get())

    def save(self):
        APIModel.save(self)
        for entry in self.entries:
            entry.save()
        return self

    def add_entry(self, weight, description, explanation=''):
        """
        Adds an entry to this rubric but does not save it. Rubric must already exist
        """
        entry = RubricEntry(rubric_id=self.id, weight=weight, description=description, explanation=explanation)
        self.entries.append(entry)
        return entry

    def create_evaluation(self, user_id, submission_id, entry_values):
        # TODO: When async API is implemented, entries should be created in a callback
        evaluation = Evaluation(rubric_id=self.id, user_id=user_id, submission_id=submission_id)
        for entry in self.entries:
            present = False
            if entry.id in entry_values:
                present = entry_values[entry.id]
            evaluation.add_entry(entry.id, present)
        evaluation.save()
        return evaluation

class RubricEntry(APIModel):
    __attributes__ = ['rubric_id', 'description', 'explanation', 'weight']
    __slots__ = __attributes__
    __base_url__ = 'entries'
    def url(self):
        if self.id:
            return slumber.url_join('rubrics', self.rubric_id, 'entries', self.id)
        else:
            return slumber.url_join('rubrics', self.rubric_id, 'entries')

    @property
    def json_root(self):
      return 'rubric_entry'

class GradingConfiguration(APIModel):
    __attributes__ = ['due_date', 'evaluations_per_submission', 'evaluations_per_grader',
                      'open_date', 'priority_weights', 'question_id', 'training_exercises_required']
    __slots__ = __attributes__
    __base_url__ = 'grading_configuration'

    def url(self):
        return slumber.url_join('questions', self.question_id, 'grading_configuration')
    @property
    def json_root(self):
      return 'grading_configuration'

class Group(APIModel):
    __attributes__ = ['title']
    __slots__ = __attributes__ + ['memberships']
    __base_url__ = 'groups'
    def __init__(self, **kwargs):
        memberships = kwargs.pop('memberships', None)
        self.update_attributes(**kwargs)
        if memberships:
            print memberships
            self.save()
            self.memberships = [GroupMembership(**data).save() for data in memberships]
        else:
            self.memberships = []

    def get_memberships(self):
        memberships = API.groups(self.id).memberships.get()
        self.memberships = [GroupMembership(**data) for data in memberships]

    def add_user(self, user):
        membership = GroupMembership(group_id=self.id, user_id=user.id)
        membership.save()
        return membership
        #GroupMembership(**API.groups(self.id).memberships.post({'membership':{'user_id':user.id}}))
    def remove_user(self, user):
        """
        The proper way to remove a user from a group would be to have the membership_id ahead of time by eg. clicking on
        a user from a list. This operation could be done much more easily on the service side.
        """
        membership_id = next((x.id for x in self.memberships if x.user_id == user.id), None)
        if membership_id:
            API.groups(self.id).memberships(membership_id).delete()
    @staticmethod
    def get_by_id(id, include_members=True):
        g = Group(**API.groups(id).get(include_members=('1' if include_members else '0')))
        return g

class GroupMembership(APIModel):
    __attributes__ = ['user_id', 'group_id']
    __slots__ = __attributes__
    __base_url__ = 'memberships'
    @property
    def json_root(self):
        return 'membership'
    def url(self):
        if self.id:
            return slumber.url_join('groups', self.group_id, 'memberships', self.id)
        else:
            return slumber.url_join('groups', self.group_id, 'memberships')
    def to_json(self):
        attributes = dict([(key, getattr(self,key, None)) for key in self.__attributes__ if hasattr(self, key)])
        attributes.pop('group_id', None)
        return json.dumps({self.json_root:attributes})

class GroupRole(APIModel):
    __attributes__ = ['question_id', 'group_id', 'role']
    __slots__ = __attributes__
    __base_url__ = 'group_roles'
    (SUBMITTER, GRADER, ADMIN) = (0, 1, 2)
    def url(self):
        if self.id:
            return slumber.url_join('questions', self.question_id, 'group_roles', self.id)
        else:
            return slumber.url_join('questions', self.question_id, 'group_roles')
    @property
    def json_root(self):
        return 'group_role'
    def to_json(self):
        attributes = dict([(key, getattr(self,key, None)) for key in self.__attributes__ if hasattr(self, key)])
        attributes.pop('question_id', None)
        return json.dumps({self.json_root: attributes})

class Example(APIModel):
    __attributes__ = ['gquestion_id', 'submission_id', 'user_id']
    __slots__ = __attributes__
    __base_url__ = 'examples'
    def url(self):
        if self.id:
            return slumber.url_join('questions'. self.question_id, 'examples', self.id)
        else:
            return slumber.url_join('questions'. self.question_id, 'examples')
    @property
    def json_root(self):
        return 'example'
    def to_json(self):
        attributes = dict([(key, getattr(self,key, None)) for key in self.__attributes__ if hasattr(self, key)])
        attributes.pop('question_id', None)
        return json.dumps({self.json_root: attributes})

class Evaluation(APIModel):
    __attributes__ = ['rubric_id', 'user_id', 'submission_id', 'comments', 'offset']
    __slots__ = __attributes__ + ['entries']
    __base_url = 'evaluations'

    def url(self):
        if self.id:
            return slumber.url_join('evaluations', self.id)
        else:
            return slumber.url_join('evaluations')

    def add_entry(self, rubric_entry_id, value):
        if not hasattr(self, 'entries'):
            self.entries = {}
        self.entries[rubric_entry_id]=value

    def to_json(self):
        attributes = dict([(key, getattr(self,key, None)) for key in self.__attributes__ if hasattr(self, key)])
        entries_attributes = []
        
        for entry_id, value in self.entries.items():
            entries_attributes.append({'rubric_entry_id': entry_id, 'present': value})
        return json.dumps({self.json_root: attributes, 'entries_attributes':entries_attributes})

class RubricEntryValue(APIModel):
    """
    This is weird, because you have to set the entries as a child of the evaluation
    but there's no way to access them individually. Maybe this shouldn't be a class.
    """
    __attributes__ = ['rubric_entry_id', 'evaluation_id', 'present']
    __slots__ = __attributes__
    @property
    def json_root(self):
      return 'rubric_entry_value'

class Task(APIModel):
    __attributes__ = ['grader_id', 'submission_id', 'question_id', 'completed']
    __slots__ = __attributes__

class GradingQueue(APIModel):
    __attributes__ = ['question_id']
    def __init__(self, question, **kwargs):
        self.question = question
        self.question_id = question.id

    def url(self):
        return slumber.url_join(HOST, 'questions', self.question_id, 'grading_queue')
    def request_work_for_user(self, user):
        # TODO: Move this to grading_queue_controller? More sensical that way
        url = slumber.url_join(HOST, 'questions', self.question_id, 'tasks', 'request_work')
        params = {'user_id':user.id}
        response = requests.post(url, params)
        if response.status_code == 200:
            if len(response.json)>0:
                return [ Task(**data) for data in response.json ]

