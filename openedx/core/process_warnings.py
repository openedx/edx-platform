import json
import os
import io
import pprint
import re
import pdb
import argparse
import pandas as pd
from write_to_html import HtmlOutlineWriter
from collections import Counter

columns =  ['message', 'category', 'filename', 'lineno', 'high_location', 'label', 'num','deprecated']
columns_index_dict = {key: index for index, key in enumerate(columns)}


pp = pprint.PrettyPrinter(indent=4, depth=2)


def seperate_warnings_by_location(warnings_data):
    """
    Warnings originate from multiple locations, this function takes in list of warning objects 
    and seperates them based on their filename location
    """

    # first create regex for each know file location
    warnings_locations = {
        ".*/python\d\.\d/site-packages/.*\.py": "python",
        ".*/edx-platform/lms/.*\.py": "lms",
        ".*/edx-platform/openedx/.*\.py": "openedx",
        ".*/edx-platform/cms/.*\.py": "cms",
        ".*/edx-platform/common/.*\.py": "common",
    }

    """
    seperate into locations
    flow:
     iterate through each wanring_object, see if its filename matches any regex in warning locations.
     If so, change high_location index on warnings_object to location name
    """
    for warnings_object in warnings_data:
        warning_origin_located = False
        for key in warnings_locations:
            if re.search(key, warnings_object[columns_index_dict["filename"]]) != None:
                warnings_object[columns_index_dict["high_location"]] = warnings_locations[key]
                warning_origin_located = True
                break
        if not warning_origin_located:
            warnings_object[columns_index_dict["high_location"]] = "other"
    return warnings_data

def convert_warning_dict_to_list(warning_dict):
    #namedtuple('message', 'category', 'filename', 'lineno', 'high_location', 'label', 'num')
    output = []
    for index, column in enumerate(columns):
        if column in warning_dict:
            if column == 'message' and "unclosed" in warning_dict[column]:
                None
                # pdb.set_trace()
            output.append(warning_dict[column])
        else:
            output.append(None)
    output[columns_index_dict["num"]] = 1
    return output


def read_warning_data(dir_path):
    """
    During test runs in jenkins, multiple warning json files are output. This function finds all files
    and aggregates the warnings in to one large list
    """
    # pdb.set_trace()
    dir_path = os.path.expanduser(dir_path)
    # find all files that exist in given directory
    files_in_dir = [
        f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path, f))
    ]
    warnings_files = []

    # TODO(jinder): currently this is hardcoded in, maybe create a constants file with info
    # THINK(jinder): but creating file for one constant seems overkill
    warnings_file_name_regex = "pytest_warnings_?\d*\.json"

    # iterate through files_in_dir and see if they match our know file name pattern
    for file in files_in_dir:
        if re.search(warnings_file_name_regex, file) != None:
            warnings_files.append(file)

    # go through each warning file and aggregate warnigns into warnings_data
    warnings_data = []
    for file in warnings_files:
        with open(os.path.expanduser(dir_path + "/" + file), "r") as read_file:
            json_input = json.load(read_file)
            if "warnings" in json_input:
                data =[convert_warning_dict_to_list(warning_dict) for warning_dict in json_input["warnings"]]
                warnings_data.extend(data)
            else:
                print(file)
    return warnings_data

def compress_similar_warnings(warnings_data):
    tupled_data = [tuple(data) for data in warnings_data]
    test_counter = Counter(tupled_data)
    output = [list(value) for value in test_counter.keys()]
    for data_object in output:
        data_object[columns_index_dict["num"]] = test_counter[tuple(data_object)]
    return output



def process_warnings_json(dir_path):
    """
    Master function to process through all warnings and output a dict

    dict structure:
    {
        location: [{warning text: {file_name: warning object}}]
    }

    flow:
        Aggregate data from all warning files
        Seperate warnings by deprecated vs non deprecated(has word deprecate in it)
        Further categorize warnings
        Return output
    Possible Error/enchancement: there might be better ways to seperate deprecates vs
        non-deprecated warnings
    """
    warnings_data = read_warning_data(dir_path)
    for warnings_object in warnings_data:
        if "deprecated" in warnings_object[columns_index_dict["message"]]:
            warnings_object[columns_index_dict["deprecated"]] = True
        else:
            warnings_object[columns_index_dict["deprecated"]] = False
    warnings_data = seperate_warnings_by_location(warnings_data)
    compressed_warnings_data = compress_similar_warnings(warnings_data)
    return compressed_warnings_data



def group_and_sort_by_sumof(dataframe, group, sort_by):
    groups_by = dataframe.groupby(group)
    temp_list_to_sort = [(key,value,value[sort_by].sum()) for key, value in groups_by]
        #sort by count
    return sorted(temp_list_to_sort, key = lambda x: -x[2])

def write_html_report(warnings_dataframe, html_path):
    """
    """
    html_path = os.path.expanduser(html_path)
    with io.open(html_path, "w") as fout:
        html_writer = HtmlOutlineWriter(fout)
        category_sorted_by_count = group_and_sort_by_sumof(warnings_dataframe, "category", "num")
        for category, group_in_category, category_count in category_sorted_by_count:
            html = u'<span class="count">{category}, count: {count}</span> '.format(category=category,count=category_count)
            html_writer.start_section(html, klass=u"category")
            locations_sorted_by_count = group_and_sort_by_sumof(group_in_category, "high_location", "num")

            for location, group_in_location, location_count in locations_sorted_by_count:
                # pp.pprint(location)
                html = u'<span class="count">{location}, count: {count}</span> '.format(location=location,count=location_count)
                html_writer.start_section(html, klass=u"location")
                message_group_sorted_by_count = group_and_sort_by_sumof(group_in_location, "message", "num")
                # pdb.set_trace()
                for message, message_group, message_count in message_group_sorted_by_count:
                    # pp.pprint(warning_text)
                    html = u'<span class="count">{warning_text}, count: {count}</span> '.format(
                        warning_text=message, count=message_count
                    )
                    html_writer.start_section(html, klass=u"warning_text")
                    # warnings_object[location][warning_text] is a list
                    for index, warning in message_group.iterrows():
                        # pp.pprint(warning)
                        html = u'<span class="count">{warning_file_path}</span> '.format(
                            warning_file_path=warning["filename"]
                        )
                        html_writer.start_section(html, klass=u"warning")

                        html = u'<p class="lineno">lineno: {lineno}</p> '.format(
                            lineno=warning["lineno"]
                        )
                        html_writer.write(html)
                        html = u'<p class="num">num_occur: {num}</p> '.format(
                            num=warning["num"]
                        )
                        html_writer.write(html)

                        html_writer.end_section()
                    html_writer.end_section()
                html_writer.end_section()
            html_writer.end_section()

parser = argparse.ArgumentParser(
    description="Process and categorize pytest warnings and output html report."
)
parser.add_argument("--dir_path", default="test_root/log")
parser.add_argument("--html_path", default="test_html.html")
args = parser.parse_args()
output = process_warnings_json(args.dir_path)
warnings_dataframe = pd.DataFrame(data = output, columns=columns)
write_html_report(warnings_dataframe, args.html_path)

