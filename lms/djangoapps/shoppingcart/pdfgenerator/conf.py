# -*- coding: utf-8 -*-
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(os.path.join(__file__)))

LANGUAGE = 'cs'

try:
    import gettext
    path =  os.path.join(PROJECT_ROOT, 'locale')
    t = gettext.translation('messages', path, languages=[LANGUAGE],
                            codeset='utf8')

    _ = lambda message: t.gettext(message).decode('utf8')
except IOError:
    _ = lambda x: x
    print "Fix this!"
except ImportError:
    _ = lambda x: x

FONT_PATH = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf'
FONT_BOLD_PATH = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans-Bold.ttf'
