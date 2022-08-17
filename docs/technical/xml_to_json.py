import xml.etree.ElementTree as ET
import json


def parse_desc(n):
    return n.text


def parse_source(n):
    return n[0].items()[0][1]


def parse_def(n):
    return n[0].text


def iter_toggle(section):
    key = {"name": section[0].text}
    for item in section[1:]:
        if item.items()[0][1] == "source":
            key["source"] = parse_source(item)
        elif item.items()[0][1] == "default":
            key["default"] = parse_def(item)
        elif item.items()[0][1] == "warning":
            key["warning"] = item[0].text
        elif item.items()[0][1] == "description":
            key["desc"] = parse_desc(item)
        else:
            key[item.items()[0][1]] = item.text.split(": ")[1]
    return key


result = {}

s = ET.parse("_build/xml/settings.xml")
s = s.getroot()
s = s[0]

scms = s.findall("section")[1]
slms = s.findall("section")[0]

lms_settings = []
cms_settings = []

for i in scms[1:]:
    cms_settings.append(iter_toggle(i))

result["cms_settigs"] = cms_settings

for i in slms[1:]:
    lms_settings.append(iter_toggle(i))

result["lms_settings"] = lms_settings

f = ET.parse("_build/xml/featuretoggles.xml")
f = f.getroot()
f = f[1]

f_a = []

for i in f[2:]:
    f_a.append(iter_toggle(i))

result["features_toggles"] = f_a
raw_json = json.dumps(result, indent=2, ensure_ascii=False)
result_file = open("result.json", "wt")
result_file.write(raw_json)
result_file.close()
