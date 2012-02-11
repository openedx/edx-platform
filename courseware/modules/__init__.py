import os
import os.path

from django.conf import settings

import capa_module
import html_module
import schematic_module
import seq_module
import template_module
import vertical_module
import video_module

# Import all files in modules directory, excluding backups (# and . in name) 
# and __init__
#
# Stick them in a list
modx_module_list = []

for f in os.listdir(os.path.dirname(__file__)):
    if f!='__init__.py' and \
            f[-3:] == ".py" and \
            "." not in f[:-3] \
            and '#' not in f:
        mod_path = 'courseware.modules.'+f[:-3]
        mod = __import__(mod_path, fromlist = "courseware.modules")
        if 'Module' in mod.__dict__:
            modx_module_list.append(mod)

# Convert list to a dictionary for lookup by tag
modx_modules = {}
for module in modx_module_list:
    for tag in module.Module.get_xml_tags():
        modx_modules[tag] = module.Module

def get_module_class(tag):
    return modx_modules[tag]

