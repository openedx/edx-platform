import os
import csv
from datetime import datetime
import pandas as pd

directory = '/edx/var/edxapp/uploads/'

lms2019_converter = {
    'Progess test (Avg)': 'Progress test (Avg)',
    'Quiz 1:': 'Quiz 1',
    'Quiz 2:': 'Quiz 2',
    'Quiz 3:': 'Quiz 3',
    'Quiz 4:': 'Quiz 4',
    'Quiz 5:': 'Quiz 5',
    'Quiz 6:': 'Quiz 6',
    'Quiz 7:': 'Quiz 7',
    'Quiz 8:': 'Quiz 8',
    'Quiz 9:': 'Quiz 9',
    'Quiz 10:': 'Quiz 10',
    'Quiz 11:': 'Quiz 11',
    'Quiz 12:': 'Quiz 12',
    'Quiz 13:': 'Quiz 13',
    'Quiz 14:': 'Quiz 14',
    'Quiz 15:': 'Quiz 15',
    'Quiz 16:': 'Quiz 16',
    'Quiz 17:': 'Quiz 17',
    'Quiz 18:': 'Quiz 18',
    'Quiz 19:': 'Quiz 19',
    'Quiz 20:': 'Quiz 20',
    'Quiz 21:': 'Quiz 21',
    'Quiz 22:': 'Quiz 22',
    'Quiz 23:': 'Quiz 23',
    'Quiz 24:': 'Quiz 24',
    'Quiz 25:': 'Quiz 25',
    'Quiz 26:': 'Quiz 26',
    'Quiz 27:': 'Quiz 27',
    'Quiz 28:': 'Quiz 28',
    'Quiz 29:': 'Quiz 29',
    'Quiz 30:': 'Quiz 30',
    'Quiz 31:': 'Quiz 31',
    'Quiz 32:': 'Quiz 32',
    'Quiz 33:': 'Quiz 33',
    'Quiz 34:': 'Quiz 34',
    'Quiz 35:': 'Quiz 35',
    'Quiz 36:': 'Quiz 36',
    'Quiz 37:': 'Quiz 37',
    'Quiz 38:': 'Quiz 38',
    'Quiz 39:': 'Quiz 39',
    'Quiz 40:': 'Quiz 40',
    'Progess test': 'PT 1',
    'Progess test 1:': 'PT 1',
    'Progess test 2:': 'PT 2',
    'Progess test 3:': 'PT 3',
    'Progess test 4:': 'PT 4',
    'Progess test 5:': 'PT 5',
    'Progess test 6:': 'PT 6',
    'Progess test 7:': 'PT 7',
    'Progess test 8:': 'PT 8',
    'Progess test 9:': 'PT 9',
    'Progess test 10:': 'PT 10',
    'Progress test': 'PT 1',
    'Progress test 1:': 'PT 1',
    'Progress test 2:': 'PT 2',
    'Progress test 3:': 'PT 3',
    'Progress test 4:': 'PT 4',
    'Progress test 5:': 'PT 5',
    'Progress test 6:': 'PT 6',
    'Progress test 7:': 'PT 7',
    'Progress test 8:': 'PT 8',
    'Progress test 9:': 'PT 9',
    'Progress test 10:': 'PT 10',
    'Lab 1:': 'Lab 1',
    'Lab 2:': 'Lab 2',
    'Lab 3:': 'Lab 3',
    'Lab 4:': 'Lab 4',
    'Lab 5:': 'Lab 5',
    'Lab 6:': 'Lab 6',
    'Lab 7:': 'Lab 7',
    'Lab 8:': 'Lab 8',
    'Lab 9:': 'Lab 9',
    'Lab 10:': 'Lab 10',
    'Project 1:': 'Project 1',
    'Project 2:': 'Project 2',
    'Project 3:': 'Project 3',
    'Project 4:': 'Project 4',
    'Project 5:': 'Project 5',
}

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

def process_grade_file(files):
	lms_version = 'lms2022'
	partner = 'FUNiX'

	all_filenames = []
	for fullpath in files:
		# get file name from full_path by split
		file = fullpath.split('/')[-1]

		org = file[:file.find('_', 0)]
		course = file[file.find('_', 0) + 1 : file.find('_grade_report')]

		with open(fullpath, encoding='utf-8') as csv_file:
			csv_reader = csv.reader(csv_file, delimiter=',')

			# Add two more columns: Org and Course at the beginning of the csv file
			output_file = os.path.join(directory, 'Done_' + file)
			all_filenames.append(output_file)

			output_csv = open(output_file, 'w', newline='')
			csv_writer = csv.writer(output_csv)
			line = 0

			for row in csv_reader:
				if line == 0:
					row.insert(0, 'Course')
					row.insert(0, 'Org')
					row.insert(0, 'LMS Version')
					row.insert(0, 'Partner')

					# Consolidate column title to odoo field-friendly
					col_no = 0
					for col in row:
						for key in lms2019_converter:
							if col.startswith(key):
								row[col_no] = lms2019_converter[key]

						col_no += 1
				else:
					row.insert(0, course)
					row.insert(0, org)
					row.insert(0, lms_version)
					row.insert(0, partner)

				csv_writer.writerow(row)
				line += 1
			output_csv.close()

	return all_filenames

def merge_all_csv(files):
    combined_csv = pd.concat([pd.read_csv(f) for f in files])

    # Write to a new file with name = 'combined_csv' and timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    combined_csv_path = os.path.join(directory, 'combined_csv_' + timestamp + '.csv')
    combined_csv.to_csv(combined_csv_path, index=False)

    # Delete all the files
    for f in files:
        os.remove(f)

    return combined_csv_path

def process_merged(combined_file):
    # create output_file with name = 'Done_combined_all.csv' and timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    output_file = os.path.join(directory, 'Done_combined_all_' + timestamp + '.csv')
    output_csv = open(output_file, 'w', newline='')
    csv_writer = csv.writer(output_csv)

    with open(combined_file) as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        header = []
        line = 0
        for row in csv_reader:
            student_id = row[4]

            # Insert new column: quiz_done, quiz_total
            if line == 0:
                header = row
                row.insert(13, 'Quiz Done')
                row.insert(14, 'Quiz Total')
            else:
                row.insert(13, '')
                row.insert(14, '')

                quiz_total = 0
                quiz_done = 0
                col_no = 0
                for col in row:
                    if not (header[col_no].startswith('Quiz (Avg)') or header[col_no].startswith('Quiz Done') or header[col_no].startswith('Quiz Total')) and header[col_no].startswith('Quiz') and col != '':
                        quiz_total += 1
                        if col == '1.0':
                            quiz_done += 1
                    col_no += 1
                
                row[13] = quiz_done
                row[14] = quiz_total

            if student_id != 'id':
                csv_writer.writerow(row)
            
            line += 1
    output_csv.close()

    # Delete the combined_file
    os.remove(combined_file)

    return output_file