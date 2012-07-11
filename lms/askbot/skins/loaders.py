import os.path
from django.template.loaders import filesystem
from django.template import RequestContext
from django.http import HttpResponse
from django.utils import translation
from django.conf import settings as django_settings
from coffin.common import CoffinEnvironment
from jinja2 import loaders as jinja_loaders
from jinja2.exceptions import TemplateNotFound
from jinja2.utils import open_if_exists
from askbot.conf import settings as askbot_settings
from askbot.skins import utils

from coffin import template
template.add_to_builtins('askbot.templatetags.extra_filters_jinja')

#module for skinning askbot
#via ASKBOT_DEFAULT_SKIN configureation variable (not django setting)

#note - Django template loaders use method django.utils._os.safe_join
#to work on unicode file paths
#here it is ignored because it is assumed that we won't use unicode paths
ASKBOT_SKIN_COLLECTION_DIR = os.path.dirname(__file__)

#changed the name from load_template_source
def filesystem_load_template_source(name, dirs=None):
    """Django template loader
    """

    if dirs is None:
        dirs = (ASKBOT_SKIN_COLLECTION_DIR, )
    else:
        dirs += (ASKBOT_SKIN_COLLECTION_DIR, )

    try:
        #todo: move this to top after splitting out get_skin_dirs()
        tname = os.path.join(askbot_settings.ASKBOT_DEFAULT_SKIN,'templates',name)
        return filesystem.load_template_source(tname,dirs)
    except:
        tname = os.path.join('default','templates',name)
        return filesystem.load_template_source(tname,dirs)
filesystem_load_template_source.is_usable = True
#added this for backward compatbility
load_template_source = filesystem_load_template_source

class SkinEnvironment(CoffinEnvironment):
    """Jinja template environment
    that loads templates from askbot skins
    """

    def __init__(self, *args, **kwargs):
        """save the skin path and initialize the
        Coffin Environment
        """
        self.skin = kwargs.pop('skin')
        super(SkinEnvironment, self).__init__(*args, **kwargs)

    def _get_loaders(self):
        """this method is not used
        over-ridden function _get_loaders that creates
        the loader for the skin templates
        """
        loaders = list()
        skin_dirs = utils.get_available_skins(selected = self.skin).values()
        template_dirs = [os.path.join(skin_dir, 'templates') for skin_dir in skin_dirs]
        loaders.append(jinja_loaders.FileSystemLoader(template_dirs))
        return loaders

    def set_language(self, language_code):
        """hooks up translation objects from django to jinja2
        environment.
        note: not so sure about thread safety here
        """
        trans = translation.trans_real.translation(language_code)
        self.install_gettext_translations(trans)

    def get_extra_css_link(self):
        """returns either the link tag (to be inserted in the html head element)
        or empty string - depending on the existence of file
        SKIN_PATH/media/style/extra.css
        """
        url = utils.get_media_url('style/extra.css', ignore_missing = True)
        if url is not None:
            return '<link href="%s" rel="stylesheet" type="text/css" />' % url
        return ''

def load_skins():
    skins = dict()
    for skin_name in utils.get_available_skins():
        skins[skin_name] = SkinEnvironment(
                                skin = skin_name,
                                extensions=['jinja2.ext.i18n',]
                            )
        skins[skin_name].set_language(django_settings.LANGUAGE_CODE)
        #from askbot.templatetags import extra_filters_jinja as filters
        #skins[skin_name].filters['media'] = filters.media
    return skins

SKINS = load_skins()

def get_skin(request = None):
    """retreives the skin environment
    for a given request (request var is not used at this time)"""
    return SKINS[askbot_settings.ASKBOT_DEFAULT_SKIN]

def get_template(template, request = None):
    """retreives template for the skin
    request variable will be used in the future to set
    template according to the user preference or admins preference

    request variable is used to localize the skin if possible
    """
    skin = get_skin(request)
    if hasattr(request,'LANGUAGE_CODE'):
        skin.set_language(request.LANGUAGE_CODE)
    return skin.get_template(template)

def render_into_skin(template, data, request, mimetype = 'text/html'):
    """in the future this function will be able to
    switch skin depending on the site administrator/user selection
    right now only admins can switch
    """
    context = RequestContext(request, data)
    template = get_template(template, request)
    return HttpResponse(template.render(context), mimetype = mimetype)

def render_text_into_skin(text, data, request):
    context = RequestContext(request, data)
    skin = get_skin(request)
    template = skin.from_string(text)
    return template.render(context)

