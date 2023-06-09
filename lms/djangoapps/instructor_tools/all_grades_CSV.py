import os

directory = '/edx/var/edxapp/uploads/'

def get_all_csv_file():
	all_dir = [x for x in os.walk(directory)]
	all_dir.pop(0)

	# all_dir = list(map(lambda x: x[2], all_dir))

	res = []

	for x in all_dir:
		root_path = x[0]

		# filter _grade_report_ file in x[2]
		files = list(filter(lambda x: '_grade_report_' in x, x[2]))

		# Sort x[2] by name reverse
		files.sort(reverse=True)

		# get the latest file
		latest_file = files[0]

		# get the latest file path
		latest_file_path = os.path.join(root_path, latest_file)
		res.append(latest_file_path)

	return res