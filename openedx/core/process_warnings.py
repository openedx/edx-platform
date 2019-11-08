import json
import os
import pprint
import re


def seperate_warnings_by_location(warnings_data):
    warnings_locations = {".*/python\d\.\d/site-packages/.*\.py":"python",  ".*/edx-platform/lms/.*\.py":"lms", ".*/edx-platform/openedx/.*\.py":"openedx", ".*/edx-platform/cms/.*\.py": "cms", ".*/edx-platform/common/.*\.py":"common"}
    warnings_by_location = {}
    for location in warnings_locations.values():
        warnings_by_location[location] = []
    # creating list for any warnings not covered by above locations
    warnings_by_location['other'] = []
    for warnings_object in warnings_data:
        warning_origin_located = False
        for key in warnings_locations:
            if re.search(key, warnings_object['filename']) != None:
                warnings_by_location[warnings_locations[key]].append(warnings_object)
                warning_origin_located = True
                break
        if not warning_origin_located:
            warnings_by_location['other'].append(warnings_object)
    return warnings_by_location

def read_warning_data(path):
    dir_path = os.path.expanduser("~/dev/edx-platform/test_root/log")
    dir_path = os.path.expanduser(path)
    files_in_dir = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))]
    warnings_file_name_regex = "warnings.*\d*\.json"
def process_warnings_json(path):
    warnings_data = {}
    with open(os.path.expanduser(path),"r") as read_file:
        warnings_data = json.load(read_file)["warnings"]
    pp = pprint.PrettyPrinter(indent=4)
    # pp.pprint(warnings_data)
    #TODO(Jinder): I've hardcoded python version here, I should use a regex instead of hardcoding these things here
    warnings_locations = {"python2.7/side-packages":"python2", "python3.5/side-packages":"python3",  "edx-platform/lms":"lms", "edx-platform/openedx":"openedx", "edx-platform/cms": "cms", "edx-platform/common":"common"}
    warning_categories = ["other", "python2", "python3", "lms", "openedx", "cms","common"]
    warnings_by_location = {}
    warnings_by_type = {'deprecated':[], 'other': []}
    deprecated_warnings = []
    non_deprecated_warnings = []
    for warnings_object in warnings_data:
        if "deprecated" in warnings_object['message']:
            deprecated_warnings.append(warnings_object)
        else:
            non_deprecated_warnings.append(warnings_object)
    
    pp.pprint(seperate_warnings_by_location(deprecated_warnings)['cms'])






path = "~/dev/edx-platform/test_root/log/warnings.json"
path = "~/Downloads/log"
read_warning_data(path)
# process_warnings_json(path)



