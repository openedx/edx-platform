import json
import os
import pprint
import re
import json2html

pp = pprint.PrettyPrinter(indent=4,depth=2)

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
    warnings_files = []
    warnings_file_name_regex = "warnings_?\d*\.json"
    for file in files_in_dir:
        if re.search(warnings_file_name_regex, file) != None:
            warnings_files.append(file)

    warnings_data = []
    for file in warnings_files:
        with open(os.path.expanduser(path + "/" + file),"r") as read_file:
            data = json.load(read_file)["warnings"]
            warnings_data.extend(data)
    return warnings_data

def process_warnings_json(path):
    warnings_data = read_warning_data(path)
    deprecated_warnings = []
    non_deprecated_warnings = []
    for warnings_object in warnings_data:
        if "deprecated" in warnings_object['message']:
            deprecated_warnings.append(warnings_object)
        else:
            non_deprecated_warnings.append(warnings_object)
    json_2_html = json2html.Json2Html()
    deprecated_output_json = seperate_warnings_by_location(deprecated_warnings)
    deprecated_warnings_html = json_2_html.convert(deprecated_output_json)
    # pp.pprint(deprecated_warnings_html)
    dir_path = os.path.expanduser(path)
    full_path = dir_path + "/test.html"
    print(full_path)
    with open(full_path, "w") as write_file:
        write_file.write(deprecated_warnings_html)
        print("hahah")







dir_path = "~/dev/edx-platform/test_root/log"
dir_path = "~/Downloads/log"
process_warnings_json(dir_path)



