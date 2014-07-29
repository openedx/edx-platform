"""
Model Managers for Course Actions
"""
from django.db import models, transaction


class CourseActionStateManager(models.Manager):
    """
    An abstract Model Manager class for Course Action State models.
    This abstract class expects child classes to define the ACTION (string) field.
    """
    # pylint: disable=no-member

    class Meta:
        abstract = True

    def find_for_course(self, course_key):
        """
        Finds and returns all entries for the given course_key and action.
        There may or may not be greater than one entry, depending on how the callers use
        this Action's model.  If the usage pattern for this Action is such that there
        should only be only one entry for a given course_key and action, then the get_for_course
        method should be used instead.
        """
        return self.filter(course_key=course_key, action=self.ACTION)

    def get_for_course(self, course_key):
        """
        Returns the entry for the given course_key and action, if found.
        Returns None if not found.
        Raises CourseActionStateException if more than 1 entry is found.
        """
        objects = self.find_for_course(course_key=course_key)
        if len(objects) == 0:
            return None
        elif len(objects) == 1:
            return objects[0]
        else:
            raise CourseActionStateException(
                message="Found more than 1 match for course_key {course_key} and action {action}: {objects}".format(
                    objects
                ),
                course_key=course_key,
                action=self.ACTION,
            )

    def delete(self, id):
        """
        Deletes the entry with given id.
        """
        self.filter(id=id).delete()


class CourseActionUIStateManager(CourseActionStateManager):
    """
    A Model Manager subclass of the CourseActionStateManager class that is aware of UI-related fields related
    to state management, including "should_display" and "message".
    """

    # add transaction protection to revert changes by get_or_create if an exception is raised before the final save.
    @transaction.commit_on_success
    def update_state(self, course_key, new_state, should_display=True, message="", user=None, allow_not_found=False):
        """
        Updates the state of the given course for this Action with the given data.
        If allow_not_found is True, automatically creates an entry if it doesn't exist.
        Raises CourseActionStateException if allow_not_found is False and an entry for the given course
            for this Action doesn't exist.
        """
        state_object, created = self.get_or_create(course_key=course_key, action=self.ACTION)

        if created:
            if allow_not_found:
                state_object.created_user = user
            else:
                raise CourseActionStateException(
                    message="No entry exists for course_key {course_key} and action {action}",
                    course_key=unicode(course_key),
                    action=self.ACTION,
                )

        # some state changes may not be user-initiated so override the user field only when provided
        if user:
            state_object.updated_user = user

        state_object.state = new_state
        state_object.should_display = should_display
        state_object.message = message
        state_object.save()
        return state_object

    def update_should_display(self, id, user, should_display):
        """
        Updates the should_display field with the given value for the entry for the given id.
        """
        self.update(id=id, updated_user=user, should_display=should_display)

    def find_all_for_display(self):
        """
        Returns all entries that have the should_display field set to True for this Action.
        """
        return self.filter(should_display=True, action=self.ACTION)


class CourseRerunUIStateManager(CourseActionUIStateManager):
    """
    A concrete model Manager for the Reruns Action.
    """
    ACTION = "rerun"

    class State(object):
        """
        An Enum class for maintaining the list of possible states for Reruns.
        """
        IN_PROGRESS = "in_progress"
        FAILED = "failed"
        SUCCEEDED = "succeeded"

    def initiated(self, course_key, user):
        """
        To be called when a new rerun is initiated for the given course by the given user.
        """
        self.update_state(
            course_key=course_key,
            new_state=self.State.IN_PROGRESS,
            user=user,
            allow_not_found=True,
        )

    def succeeded(self, course_key):
        """
        To be called when an existing rerun for the given course has successfully completed.
        """
        self.update_state(
            course_key=course_key,
            new_state=self.State.SUCCEEDED,
        )

    def failed(self, course_key, exception):
        """
        To be called when an existing rerun for the given course has failed with the given exception.
        """
        self.update_state(
            course_key=course_key,
            new_state=self.State.FAILED,
            message=exception.message,
        )


class CourseActionStateException(Exception):
    """
    An exception class for errors specific to Course Action states.
    """
    def __init__(self, course_key, action, message):
        super(CourseActionStateException, self).__init__(message.format(course_key=course_key, action=action))
