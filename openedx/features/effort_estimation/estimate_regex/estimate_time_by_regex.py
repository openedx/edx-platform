"""
Estimate time effort using regex to extract time data from text
"""

import re
import math

TIME_HOUR_REGEX = r"([0-9]+\.*[0-9]*) giờ"
TIME_MINUTE_REGEX = r"([0-9]+) phút"

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

	hour = _get_hour_time(last_line)
	minute = _get_minute_time(last_line)

	if hour != 0 or minute != 0:
		time_by_regex = math.ceil(hour * 60) + minute
		time_by_regex = math.ceil(time_by_regex / 5) * 5

	return time_by_regex
