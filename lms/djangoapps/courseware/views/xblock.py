from __future__ import absolute_import

from eventtracking import tracker
from xmodule.modulestore.django import modulestore
from xblock.exceptions import NoSuchHandlerError
from xmodule.exceptions import NotFoundError, ProcessingError
from django.http import Http404, HttpResponse
from courseware.module_render import get_module
from xmodule.modulestore.exceptions import ItemNotFoundError
from courseware.model_data import FieldDataCache
from util.json_request import JsonResponse
from xblock.django.request import django_to_webob_request, webob_to_django_response
from lazy import lazy
from opaque_keys.edx.keys import CourseKey, AsideUsageKey, UsageKey
import json
from django.conf import settings
from opaque_keys import InvalidKeyError
from xblock.core import XBlock, XBlockAside
from xmodule.x_module import XModuleDescriptor
from django.views.generic import View
import logging

log = logging.getLogger(__name__)

class XBlockHandlerView(View):
    def dispatch(self, request, course_id, block_family, usage_id, handler, suffix=None):
        if self.noauth:
            request.sure.known = False
        elif not request.user.is_authenticated():
            return HttpResponse('Unauthenticated', status=403)

        self.request = request
        self.block_family = block_family
        self.handler = handler
        self.suffix = suffix

        try:
            self.course_key = CourseKey.from_string(course_id)
        except InvalidKeyError:
            raise Http404("Invalid course id {!r}".format(course_id))

        try:
            self.usage_key = UsageKey.from_string(usage_id).map_into_course(self.course_key)
        except InvalidKeyError:
            raise Http404("Invalid usage id {!r}".format(usage_id))

        err_response = self._check_files_limits()
        if err_response is not None:
            return err_response

        if block_family in ('xblock', XBlock.entry_point, XModuleDescriptor.entry_point):
            return self.handle_xblock()
        elif block_family == XBlockAside.entry_point:
            return self.handle_xblock_aside()
        else:
            raise Http404("{!r} is an invalid block family".format(block_family))

    def handle_xblock_aside(self):
        """
        Invoke an XBlock handler, either authenticated or not.

        Arguments:
            request (HttpRequest): the current request
            course_id (str): A string of the form org/course/run
            usage_id (str): A string of the form i4x://org/course/category/name@revision
            handler (str): The name of the handler to invoke
            suffix (str): The suffix to pass to the handler when invoked
            user (User): The currently logged in user

        """
        if not isinstance(self.usage_key, AsideUsageKey):
            # TODO: This is because the usage_key and the block_family encode the same
            # information twice. But if we don't do that, then we need to dispatch on
            # the type of the UsageKey, which isn't great either.
            raise Http404("Mismatch between block family {!r} and usage id {!r}".format(
                self.block_family,
                self.usage_key
            ))

        xblock = self._load_xblock(self.usage_key.usage_key, [self.usage_key.aside_type])

        aside = xblock.runtime.get_aside_of_type(xblock, self.usage_key.aside_type)

        tracking_context_name = 'xblock_aside_handler'
        tracking_context = {
            'aside': {
                'usage_key': unicode(self.usage_key.usage_key),
                'aside_type': self.usage_key.aside_type,
            }
        }
        return self._run_handler(aside, tracking_context_name, tracking_context)

    def handle_xblock(self):
        """
        Invoke an XBlock handler, either authenticated or not.

        Arguments:
            request (HttpRequest): the current request
            course_id (str): A string of the form org/course/run
            usage_id (str): A string of the form i4x://org/course/category/name@revision
            handler (str): The name of the handler to invoke
            suffix (str): The suffix to pass to the handler when invoked
            user (User): The currently logged in user

        """
        block = self._load_xblock(self.usage_key)

        tracking_context_name = 'module_callback_handler'
        tracking_context = {
            'module': {
                'display_name': block.display_name_with_default,
            }
        }

        return self._run_handler(block, tracking_context_name, tracking_context)

    def _check_files_limits(self):
        """
        Check if the files in a request are under the limits defined by
        `settings.MAX_FILEUPLOADS_PER_INPUT` and
        `settings.STUDENT_FILEUPLOAD_MAX_SIZE`.

        Returns None if files are correct or an error messages otherwise.
        """
        self.files = self.request.FILES or {}

        for fileinput_id in self.files.keys():
            inputfiles = self.files.getlist(fileinput_id)

            # Check number of files submitted
            if len(inputfiles) > settings.MAX_FILEUPLOADS_PER_INPUT:
                msg = 'Submission aborted! Maximum %d files may be submitted at once' % \
                      settings.MAX_FILEUPLOADS_PER_INPUT
                return HttpResponse(json.dumps({'success': msg}))

            # Check file sizes
            for inputfile in inputfiles:
                if inputfile.size > settings.STUDENT_FILEUPLOAD_MAX_SIZE:  # Bytes
                    msg = 'Submission aborted! Your file "%s" is too large (max size: %d MB)' % \
                          (inputfile.name, settings.STUDENT_FILEUPLOAD_MAX_SIZE / (1000 ** 2))
                    return HttpResponse(json.dumps({'success': msg}))

        return None

    def _load_xblock(self, usage_key, asides=None):
        if asides is None:
            asides = []

        try:
            xblock = modulestore().get_item(usage_key)
        except ItemNotFoundError:
            log.warn(
                "Invalid location for course id {course_id}: {usage_key}".format(
                    course_id=self.course_key,
                    usage_key=usage_key
                )
            )
            raise Http404

        field_data_cache = FieldDataCache.cache_for_descriptor_descendents(
            self.course_key,
            self.request.user,
            xblock,
            asides=asides,
        )
        xblock = get_module(self.request.user, self.request, usage_key, field_data_cache, grade_bucket_type='ajax')
        if xblock is None:
            # Either permissions just changed, or someone is trying to be clever
            # and load something they shouldn't have access to.
            log.debug("No xblock %s for user %s -- access denied?", usage_key, self.request.user)
            raise Http404

        return xblock

    @lazy
    def _webob_request(self):
        return django_to_webob_request(self.request)

    def _run_handler(self, block, tracking_context_name, tracking_context):
        try:
            with tracker.get_tracker().context(tracking_context_name, tracking_context):
                resp = block.handle(self.handler, self._webob_request, self.suffix)

        except NoSuchHandlerError:
            log.exception("XBlock %s attempted to access missing handler %r", block, self.handler)
            raise Http404

        # If we can't find the module, respond with a 404
        except NotFoundError:
            log.exception("Module %s indicating to user that request doesn't exist", block)
            raise Http404

        # For XModule-specific errors, we log the error and respond with an error message
        except ProcessingError as err:
            log.warning("Module %s encountered an error while processing AJAX call",
                        block,
                        exc_info=True)
            return JsonResponse(object={'success': err.args[0]}, status=200)

        # If any other error occurred, re-raise it to trigger a 500 response
        except Exception:
            log.exception("Error executing xblock handler for block %s, handler %r", block, self.handler)
            raise

        return webob_to_django_response(resp)
