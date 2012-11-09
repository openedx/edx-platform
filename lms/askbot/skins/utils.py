"""utilities dealing with resolution of skin components

the lookup resolution process for templates and media works as follows:
* look up item in selected skin
* if not found look in 'default'
* raise an exception 
"""
import os
import logging
import urllib
from django.conf import settings as django_settings
from django.utils.datastructures import SortedDict
from askbot.utils import hasher

class MediaNotFound(Exception):
    """raised when media file is not found"""
    pass

def get_skins_from_dir(directory):
    """returns sorted dict with skin data, like get_available_skins
    but from a specific directory
    """
    skins = SortedDict()
    for item in sorted(os.listdir(directory)):
        item_dir = os.path.join(directory, item)
        if os.path.isdir(item_dir):
            skins[item] = item_dir
    return skins

def get_available_skins(selected=None):
    """selected is a name of preferred skin
    if it's None, then information about all skins will be returned
    otherwise, only data about selected and default skins
    will be returned

    selected skin is guaranteed to be the first item in the dictionary
    """
    skins = SortedDict()
    if hasattr(django_settings, 'ASKBOT_EXTRA_SKINS_DIR'):
        skins.update(get_skins_from_dir(django_settings.ASKBOT_EXTRA_SKINS_DIR))

    stock_dir = os.path.normpath(os.path.dirname(__file__))
    stock_skins = get_skins_from_dir(stock_dir)
    default_dir = stock_skins.pop('default')
    common_dir = stock_skins.pop('common')

    skins.update(stock_skins)
    if selected:
        if selected in skins:
            selected_dir = skins[selected]
            skins.clear()
            skins[selected] = selected_dir
        else:
            assert(selected == 'default' or selected == 'common')
            skins = SortedDict()

    #re-insert default as a last item
    skins['default'] = default_dir
    skins['common'] = common_dir 
    return skins


def get_path_to_skin(skin):
    """returns path to directory in the list of
    available skin directories that contains another
    directory called skin

    it is assumed that all skins are named uniquely
    """
    skin_dirs = get_available_skins()
    return skin_dirs.get(skin, None)

def get_skin_choices():
    """returns a tuple for use as a set of 
    choices in the form"""
    skin_names = list(reversed(get_available_skins().keys()))
    return zip(skin_names, skin_names)

def resolve_skin_for_media(media=None, preferred_skin = None):
    #see if file exists, if not, try skin 'default'
    available_skins = get_available_skins(selected = preferred_skin).items()
    for skin_name, skin_dir in available_skins:
        if os.path.isfile(os.path.join(skin_dir, 'media', media)):
            return skin_name
    raise MediaNotFound(media)

def get_media_url(url, ignore_missing = False):
    """returns url prefixed with the skin name
    of the first skin that contains the file 
    directories are searched in this order:
    askbot_settings.ASKBOT_DEFAULT_SKIN, then 'default', then 'commmon'
    if file is not found - returns None
    and logs an error message

    todo: move this to the skin environment class
    """
    #import datetime
    #before = datetime.datetime.now()
    url = urllib.unquote(unicode(url))
    while url[0] == '/': url = url[1:]

    #a hack allowing urls media stored on external locations to
    #just pass through unchanged
    if url.startswith('http://') or url.startswith('https://'):
        return url
    #todo: handles case of multiple skin directories

    #if file is in upfiles directory, then give that
    url_copy = url
    if url_copy.startswith(django_settings.MEDIA_URL[1:]):
        file_path = url_copy.replace(
                                django_settings.MEDIA_URL[1:],
                                '',
                                1
                            )
        file_path = os.path.join(
                            django_settings.MEDIA_ROOT,
                            file_path
                        )
        if os.path.isfile(file_path):
            url_copy = os.path.normpath(
                                    '///' + url_copy
                                ).replace(
                                    '\\', '/'
                                ).replace(
                                    '///', '/'
                                )
            return url_copy
        elif ignore_missing == False:
            logging.critical('missing media resource %s' % url)

    #2) if it does not exist in uploaded files directory - look in skins

    #purpose of this try statement is to determine
    #which skin is currently used
    try:
        #this import statement must be hidden here
        #because at startup time this branch will fail
        #due to an import error
        from askbot.conf import settings as askbot_settings
        use_skin = askbot_settings.ASKBOT_DEFAULT_SKIN
        resource_revision = askbot_settings.MEDIA_RESOURCE_REVISION
    except ImportError:
        use_skin = 'default'
        resource_revision = None

    #determine from which skin take the media file
    try:
        use_skin = resolve_skin_for_media(media=url, preferred_skin = use_skin)
    except MediaNotFound:
        if ignore_missing == False:
            log_message = 'missing media resource %s in skin %s' \
                            % (url, use_skin)
            logging.critical(log_message)
        return None

    url = django_settings.STATIC_URL + use_skin + '/media/' + url
    url = os.path.normpath(url).replace('\\', '/')
    
    if resource_revision:
        url +=  '?v=%d' % resource_revision

    #after = datetime.datetime.now()
    #print after - before
    return url

def update_media_revision(skin = None):
    """update skin media revision number based on the contents
    of the skin media directory"""
    from askbot.conf import settings as askbot_settings
    resource_revision = askbot_settings.MEDIA_RESOURCE_REVISION

    if skin:
        if skin in get_skin_choices():
            skin_path = get_path_to_skin(skin)
        else:
            raise MediaNotFound('Skin %s not found' % skin) 
    else:
        skin = 'default'
        skin_path = get_path_to_skin(askbot_settings.ASKBOT_DEFAULT_SKIN)

    media_dirs = [os.path.join(skin_path, 'media'),]

    if skin != 'default':
        #we have default skin as parent of the custom skin
        default_skin_path = get_path_to_skin('default')
        media_dirs.append(os.path.join(default_skin_path, 'media'))

    current_hash = hasher.get_hash_of_dirs(media_dirs)

    if current_hash != askbot_settings.MEDIA_RESOURCE_REVISION_HASH:
        askbot_settings.update('MEDIA_RESOURCE_REVISION', resource_revision + 1)
        askbot_settings.update('MEDIA_RESOURCE_REVISION_HASH', current_hash) 
        logging.debug('MEDIA_RESOURCE_REVISION changed')
    askbot_settings.MEDIA_RESOURCE_REVISION
