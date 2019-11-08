import json
import os
import pprint



def process_warnings_json(path):
    with open(os.path.expanduser(path),"r") as read_file:
        warnings_data = json.load(read_file)["warnings"]
        pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(warnings_data)
        #TODO(Jinder): I've hardcoded python version here, I should use a regex instead of hardcoding these things here
        warnings_locations = {"python2.7/side-packages":"python2", "python3.5/side-packages":"python3",  "edx-platform/lms":"lms", "edx-platform/openedx":"openedx", "edx-platform/cms": "cms", "edx-platform/common":"common"}
        warning_categories = ["other", "python2", "python3", "lms", "openedx", "cms","common"]
        warnings_by_location = {}
        warnings_by_type = {'deprecated':[], 'other': []}
        for warning_category in warning_categories:
            warnings_by_location[warning_category] = []
        for warnings_object in warnings_data:
            warning_origin_located = False
            for key in warnings_locations:
                if key in warnings_object['filename']:
                    warnings_by_location[warnings_locations[key]].append(warnings_object)
                    warning_origin_located = True
                    break
            if not warning_origin_located:
                warnings_by_location['other'].append(warnings_object)
            for key in warnings_by_type:
                if key in warnings_object['message']:
                    warnings_by_type[key].append(warnings_object)

        pp.pprint(warnings_by_type)






path = "~/dev/edx-platform/test_root/log/warnings.json"
process_warnings_json(path)



