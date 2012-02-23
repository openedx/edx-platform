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

from courseware import content_parser

# Import all files in modules directory, excluding backups (# and . in name) 
# and __init__
#
# Stick them in a list
# modx_module_list = []

# for f in os.listdir(os.path.dirname(__file__)):
#     if f!='__init__.py' and \
#             f[-3:] == ".py" and \
#             "." not in f[:-3] \
#             and '#' not in f:
#         mod_path = 'courseware.modules.'+f[:-3]
#         mod = __import__(mod_path, fromlist = "courseware.modules")
#         if 'Module' in mod.__dict__:
#             modx_module_list.append(mod)

#print modx_module_list
modx_module_list = [capa_module,  html_module,  schematic_module,  seq_module,  template_module,  vertical_module,  video_module]
#print modx_module_list

modx_modules = {}

# Convert list to a dictionary for lookup by tag
def update_modules():
    global modx_modules
    modx_modules = dict()
    for module in modx_module_list:
        for tag in module.Module.get_xml_tags():
            modx_modules[tag] = module.Module

update_modules()

def get_module_class(tag):
    ''' Given an XML tag (e.g. 'video'), return 
    the associated module (e.g. video_module.Module). 
    '''
    if tag not in modx_modules:
        update_modules()
    return modx_modules[tag]

def get_module_id(tag):
    ''' Given an XML tag (e.g. 'video'), return 
    the default ID for that module (e.g. 'youtube_id')
    '''
    return modx_modules[tag].id_attribute

def get_valid_tags():
    return modx_modules.keys()

def get_default_ids():
    tags = get_valid_tags()
    ids = map(get_module_id, tags)
    return dict(zip(tags, ids))

