"""
Estimate time effort using regex to extract time data from text
"""

import re
import math

TIME_HOUR_REGEX = r"([0-9]+\.*[0-9]*) gio"
TIME_MINUTE_REGEX = r"([0-9]+) phut"
NUMBER_REGEX = r"([0-9]+\.*[0-9]*)"

def _get_hour_time(line):
	"""
	Get hour from string
	"""
	hour = 0

	regex_result = re.findall(TIME_HOUR_REGEX, line)
	if len(regex_result) > 0:
		hour = float(regex_result[-1])

	return hour

def _get_minute_time(line):
	"""
	Get minute from string
	"""
	minute = 0

	regex_result = re.findall(TIME_MINUTE_REGEX, line)
	if len(regex_result) > 0:
		minute = int(regex_result[-1])

	return minute

def no_accent_vietnamese(s):
    s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
    s = re.sub(r'[ÀÁẠẢÃĂẰẮẶẲẴÂẦẤẬẨẪ]', 'A', s)
    s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
    s = re.sub(r'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', s)
    s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
    s = re.sub(r'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', s)
    s = re.sub(r'[ìíịỉĩ]', 'i', s)
    s = re.sub(r'[ÌÍỊỈĨ]', 'I', s)
    s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
    s = re.sub(r'[ƯỪỨỰỬỮÙÚỤỦŨ]', 'U', s)
    s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
    s = re.sub(r'[ỲÝỴỶỸ]', 'Y', s)
    s = re.sub(r'[Đ]', 'D', s)
    s = re.sub(r'[đ]', 'd', s)

    marks_list = [u'\u0300', u'\u0301', u'\u0302', u'\u0303', u'\u0306',u'\u0309', u'\u0323']

    for mark in marks_list:
        s = s.replace(mark, '')

    return s

def estimate_time_by_regex(text):
	"""Estimate time effort using regex to extract time data from text

	Args:
		text (string): Content to extract

	Returns:
		int: The time effort in minute (round by 5 min), if can't extract will return None
	"""
	lines = text.strip().split("\n")
	if len(lines) == 0:
		return None

	time_by_regex = None
	last_line = lines[-1].lower()

	last_line = no_accent_vietnamese(last_line)

	# Old method: extract minute and hour from last line
	# hour = _get_hour_time(last_line)
	# minute = _get_minute_time(last_line)

	# if hour != 0 or minute != 0:
	# 	time_by_regex = math.ceil(hour * 60) + minute
	# 	time_by_regex = math.ceil(time_by_regex / 5) * 5

	# New method: extract number from last line
	regex_result = re.findall(NUMBER_REGEX, last_line)

	# Case 1: only one result => it is hours
	if len(regex_result) == 1:
		time_by_regex = float(regex_result[-1]) * 60
	# Case 2: two result => it is hours and minutes
	elif len(regex_result) >= 2:
		time_by_regex = float(regex_result[-2]) * 60
		time_by_regex += float(regex_result[-1])
	# Case 3: no result => return None
	else:
		time_by_regex = None

	# if time is not None than round it to 5 min
	if time_by_regex is not None:
		if 'gio' in last_line or 'phut' in last_line:
			time_by_regex = math.ceil(time_by_regex / 5) * 5
		else:
			return None

	return time_by_regex
