from django.utils.translation import ugettext_lazy as _
from django.conf import settings

# Default settings.. overwrite in your own settings.py

# Planned feature.
WIKI_USE_MARKUP_WIDGET = True

####################
# LOGIN PROTECTION #
####################
# Before setting the below parameters, please note that permissions can
# be set in the django permission system on individual articles and their
# child articles. In this way you can add a user group and give them
# special permissions, be it on the root article or some other. Permissions
# are inherited on lower levels.

# Adds standard django login protection for viewing
WIKI_REQUIRE_LOGIN_VIEW = getattr(settings, 'SIMPLE_WIKI_REQUIRE_LOGIN_VIEW',
                                  False)

# Adds standard django login protection for editing
WIKI_REQUIRE_LOGIN_EDIT = getattr(settings, 'SIMPLE_WIKI_REQUIRE_LOGIN_EDIT',
                                  True)

####################
# ATTACHMENTS      #
####################

# This should be a directory that's writable for the web server.
# It's relative to the MEDIA_ROOT.
WIKI_ATTACHMENTS = getattr(settings, 'SIMPLE_WIKI_ATTACHMENTS',
                           'simplewiki/attachments/')

# If false, attachments will completely disappear
WIKI_ALLOW_ATTACHMENTS = getattr(settings, 'SIMPLE_WIKI_ALLOW_ATTACHMENTS',
                                 True)

# If WIKI_REQUIRE_LOGIN_EDIT is False, then attachments can still be disallowed
WIKI_ALLOW_ANON_ATTACHMENTS = getattr(settings, 'SIMPLE_WIKI_ALLOW_ANON_ATTACHMENTS', False)

# Attachments are automatically stored with a dummy extension and delivered
# back to the user with their original extension.
# This setting does not add server security, but might add user security
# if set -- or force users to use standard formats, which might also
# be a good idea.
# Example: ('pdf', 'doc', 'gif', 'jpeg', 'jpg', 'png')
WIKI_ATTACHMENTS_ALLOWED_EXTENSIONS = getattr(settings, 'SIMPLE_WIKI_ATTACHMENTS_ALLOWED_EXTENSIONS',
                                              None)

# At the moment this variable should not be modified, because
# it breaks compatibility with the normal Django FileField and uploading
# from the admin interface.
WIKI_ATTACHMENTS_ROOT = settings.MEDIA_ROOT

# Bytes! Default: 1 MB.
WIKI_ATTACHMENTS_MAX = getattr(settings, 'SIMPLE_WIKI_ATTACHMENTS_MAX',
                               1 * 1024 * 1024)

# Allow users to edit titles of pages
# (warning! titles are not maintained in the revision system.)
WIKI_ALLOW_TITLE_EDIT = getattr(settings, 'SIMPLE_WIKI_ALLOW_TITLE_EDIT', False)

# Global context processors
# These are appended to TEMPLATE_CONTEXT_PROCESSORS in your Django settings
# whenever the wiki is in use. It can be used as a simple, but effective
# way of extending simplewiki without touching original code (and thus keeping
# everything easily maintainable)
WIKI_CONTEXT_PREPROCESSORS = getattr(settings, 'SIMPLE_WIKI_CONTEXT_PREPROCESSORS',
                                     ())

####################
# AESTHETICS       #
####################

# List of extensions to be used by Markdown. Custom extensions (i.e., with file
# names of mdx_*.py) can be dropped into the simplewiki (or project) directory
# and then added to this list to be utilized. Wikilinks is always enabled.
#
# For more information, see
# http://www.freewisdom.org/projects/python-markdown/Available_Extensions
WIKI_MARKDOWN_EXTENSIONS = getattr(settings, 'SIMPLE_WIKI_MARKDOWN_EXTENSIONS',
                           ['footnotes',
                            'tables',
                            'headerid',
                            'fenced_code',
                            'def_list',
                            'codehilite',
                            'abbr',
                            'toc',
                            'camelcase', # CamelCase-style wikilinks
                            'video',      # In-line embedding for YouTube, etc.
                            #'image'       # In-line embedding for images - too many bugs. It has a failed REG EXP.
                            ])


WIKI_IMAGE_EXTENSIONS       = getattr(settings, 
                                'SIMPLE_WIKI_IMAGE_EXTENSIONS',
                                ('jpg','jpeg','gif','png','tiff','bmp'))
# Planned features
WIKI_PAGE_WIDTH             = getattr(settings, 
                                'SIMPLE_WIKI_PAGE_WIDTH', "100%")
                                
WIKI_PAGE_ALIGN             = getattr(settings, 
                                'SIMPLE_WIKI_PAGE_ALIGN', "center")
                                
WIKI_IMAGE_THUMB_SIZE       = getattr(settings, 
                                'SIMPLE_WIKI_IMAGE_THUMB_SIZE', (200,150))
                                
WIKI_IMAGE_THUMB_SIZE_SMALL = getattr(settings, 
                                'SIMPLE_WIKI_IMAGE_THUMB_SIZE_SMALL', (100,100))
