"""Code run at server start up to initialize the lti_provider app."""

# Import the tasks module to ensure that signal handlers are registered.
import lms.djangoapps.lti_provider.tasks        # pylint: disable=unused-import
