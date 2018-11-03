import pandas as pd
from nbgrader.api import Gradebook, MissingEntry

# Create the connection to the database
with Gradebook('sqlite:///gradebook.db') as gb:

    grades = []

    # Loop over each assignment in the database
    for assignment in gb.assignments:

        # Loop over each student in the database
        for student in gb.students:

            # Create a dictionary that will store information about this student's
            # submitted assignment
            score = {}
            score['max_score'] = assignment.max_score
            score['student'] = student.id
            score['assignment'] = assignment.name

            # Try to find the submission in the database. If it doesn't exist, the
            # `MissingEntry` exception will be raised, which means the student
            # didn't submit anything, so we assign them a score of zero.
            try:
                submission = gb.find_submission(assignment.name, student.id)
            except MissingEntry:
                score['score'] = 0.0
            else:
                score['score'] = submission.score

            grades.append(score)

    # Create a pandas dataframe with our grade information, and save it to disk
    grades = pd.DataFrame(grades).set_index(['student', 'assignment']).sortlevel()
    grades.to_csv('grades.csv')

    # Print out what the grades look like
    with open('grades.csv', 'r') as fh:
        print(fh.read())
