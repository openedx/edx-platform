"""
Module that allows to insert LTI tools to page.

Module uses current 0.14.2 version of requests (oauth part).
Please update code when upgrading requests.

Protocol is oauth1, LTI version is 1.1.1:
http://www.imsglobal.org/LTI/v1p1p1/ltiIMGv1p1p1.html
"""

import logging
import requests
import urllib

from xmodule.editing_module import MetadataOnlyEditingDescriptor
from xmodule.x_module import XModule
from pkg_resources import resource_string
from xblock.core import String, Scope, List

log = logging.getLogger(__name__)


class LTIFields(object):
    """provider_url and tool_id together is unique location of LTI in the web.

    Scope settings should be scope content. Expanation by Cale:
    "There is no difference in presentation to the user yet because
    there is no sharing between courses.  However, when we get to the point of being
    able to have multiple courses using the same content,
    then the distinction between Scope.settings (local to the current course),
    and Scope.content (shared across all uses of this content in any course)
    becomes much more clear/necessary."
    """
    # client_key = String(help="Client key", default='', scope=Scope.settings)
    # client_secret = String(help="Client secret", default='', scope=Scope.settings)
    lti_id = String(help="Id of the tool", default='', scope=Scope.settings)
    launch_url = String(help="URL of the tool", default='', scope=Scope.settings)
    custom_parameters = List(help="Custom parameters", scope=Scope.settings)


class LTIModule(LTIFields, XModule):
    '''LTI Module'''

    js = {'js': [resource_string(__name__, 'js/src/lti/lti.js')]}
    css = {'scss': [resource_string(__name__, 'css/lti/lti.scss')]}
    js_module_name = "LTI"

    def get_html(self):
        """ Renders parameters to template. """

        # get client_key and client_secret parameters from current course:
        # course location example: u'i4x://blades/1/course/2013_Spring'
        course = self.descriptor.system.load_item(
            self.location.tag + '://' + self.location.org + '/' +
            self.location.course + '/course' + '/2013_Spring')
        client_key, client_secret = '', ''
        for lti_passport in course.LTIs:
            try:
                lti_id, key, secret = lti_passport.split(':')
            except ValueError:
                raise Exception('Could not parse LTI passport: {0}. \
                    Should be "id:key:secret" string.'.format(lti_passport))
            if lti_id == self.lti_id:
                client_key, client_secret = key, secret
                break

        # these params do not participate in oauth signing
        params = {
            'launch_url': self.launch_url,
            'element_id': self.location.html_id(),
            'element_class': self.location.category,
        }

        parsed_custom_parameters = {}
        for custom_parameter in self.custom_parameters:
            try:
                param_name, param_value = custom_parameter.split('=')
            except ValueError:
                raise Exception('Could not parse custom parameter: {0}. \
                    Should be "x=y" string.'.format(custom_parameter))

            # LTI specs:  'custom_' should be prepended before each custom parameter
            parsed_custom_parameters.update(
                {u'custom_' + unicode(param_name): unicode(param_value)}
            )

        params.update({'custom_parameters': parsed_custom_parameters})
        params.update(self.oauth_params(
            parsed_custom_parameters,
            client_key,
            client_secret
        ))
        return self.system.render_template('lti.html', params)

    def oauth_params(self, custom_parameters, client_key, client_secret):
        """Obtains LTI html from provider"""
        client = requests.auth.Client(
            client_key=unicode(client_key),
            client_secret=unicode(client_secret)
        )

        # @ned - why  self.runtime.anonymous_student_id is None in dev env?
        user_id = self.runtime.anonymous_student_id
        user_id = user_id if user_id else 'default_user_id'

        # must have parameters for correct signing from LTI:
        body = {
            'user_id': user_id,
            'oauth_callback': 'about:blank',
            'lis_outcome_service_url': '',
            'lis_result_sourcedid': '',
            'launch_presentation_return_url': '',
            'lti_message_type': 'basic-lti-launch-request',
            'lti_version': 'LTI-1p0',
            'role': 'student'
        }

        # appending custom parameter for signing
        body.update(custom_parameters)

        # This is needed for body encoding:
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        _, headers, _ = client.sign(
            unicode(self.launch_url),
            http_method=u'POST',
            body=body,
            headers=headers)
        params = headers['Authorization']
        # parse headers to pass to template as part of context:
        params = dict([param.strip().replace('"', '').split('=') for param in params.split('",')])

        params[u'oauth_nonce'] = params[u'OAuth oauth_nonce']
        del params[u'OAuth oauth_nonce']

        params['user_id'] = body['user_id']

        # 0.14.2 (current) version of requests oauth library encodes signature,
        # with 'Content-Type': 'application/x-www-form-urlencoded'
        # so '='' becomes '%3D'.
        # We send form via browser, so browser will encode it again,
        # So we need to decode signature back:
        params[u'oauth_signature'] = urllib.unquote(params[u'oauth_signature']).decode('utf8')

        return params


class LTIModuleDescriptor(LTIFields, MetadataOnlyEditingDescriptor):
    """LTI Descriptor. No export/import to xml."""
    module_class = LTIModule
