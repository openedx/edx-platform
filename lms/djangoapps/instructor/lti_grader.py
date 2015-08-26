"""
Send grades to an OpenEdX LTI component
"""
import csv
import tempfile

from django.utils.translation import ugettext as _

from instructor import lti_connection


class LTIGrader(object):
    """
    Updates grades for a given LTI component
    """

    def __init__(self, course_id, url_base, lti_key, lti_secret):
        self.url_base = url_base
        self.course_id = course_id
        self.key = lti_key
        self.secret = lti_secret
        self.output = {'success': [], 'error': []}

    def _get_first_anon_id(self, grade_data):
        """
        Returns the first anonymized student id for in the given uploaded csv data file
        :param grade_data: an InMemoryUploadedFile with lti grade data
        :return: anon_id
        """
        reader = self._unicode_csv_reader(grade_data)
        try:
            # discard the header row
            reader.next()
            first_row = reader.next()
            anon_id = first_row[1]
            grade_data.seek(0)
        except StopIteration:
            self.output['error'].append(_('The CSV file contains no useful data!'))
            anon_id = None
        return anon_id

    def update_grades(self, source):
        """
        Updates grades for the LTI component with the grade data provided
        :param grade_data: an InMemoryUploadedFile with lti grade data
        :return: output, a dictionary with two keys: 'success' and 'error'
        """
        grade_data = tempfile.TemporaryFile()
        for chunk in source.chunks():
            grade_data.write('\n'.join(chunk.splitlines()))
        grade_data.seek(0)
        first_anon_id = self._get_first_anon_id(grade_data)
        if first_anon_id is None:
            return self.output
        test_url = self.url_base + first_anon_id
        credentials_are_valid = lti_connection.validate_lti_passport(self.key, self.secret, test_url)
        if not credentials_are_valid:
            self.output['error'].append(_("LTI passport sanity check failed. Your lti_key ({key}) or lti_secret ({secret}) are probably incorrect.").format(
                key=self.key,
                secret=self.secret,
            ))
            grade_data.close()
            return self.output

        for grade_row in self._generate_valid_grading_rows(grade_data):
            result = lti_connection.post_grade(self.url_base, self.key, self.secret, grade_row)
            if result[0]:
                self.output['success'].append(
                    _("Grade post successful: user id {user_id} (email: {email}).").format(
                        user_id=result[1],
                        email=result[2],
                    )
                )
            else:
                self.output['error'].append(
                    _("Grade post failed: user id {user_id} (email: {email}).").format(
                        user_id=result[1],
                        email=result[2],
                    )
                )
        grade_data.close()
        return self.output

    def _generate_valid_grading_rows(self, data):
        """
        Yield valid grading rows from a file
        """
        reader = self._unicode_csv_reader(data)
        for row_number, row in enumerate(reader):

            #skip the header row
            if row_number == 0:
                continue

            if len(row) < 5:
                self.output['error'].append(_("Bad row: grading_csv row {row_number} ({row}) doesn't have enough info").format(
                    row_number=row_number,
                    row=row,
                ))
                continue
            try:
                if len(row) == 5:
                    yield tuple([
                        int(row[0]),
                        unicode(row[1]),
                        unicode(row[2]),
                        float(row[3]),
                        float(row[4]),
                        unicode(''),
                    ])
                else:
                    yield tuple([
                        int(row[0]),
                        unicode(row[1]),
                        unicode(row[2]),
                        float(row[3]),
                        float(row[4]),
                        unicode(row[5]),
                    ])
            except ValueError:
                self.output['error'].append(_("Bad row: grading_csv row {row_number} ({row}) has bad values").format(
                    row_number=row_number,
                    row=row,
                ))

    def _unicode_csv_reader(self, unicode_csv_data, dialect=csv.excel, **kwargs):
        """
        Yield CSV entries as UTF-8 encoded strings; see https://docs.python.org/2/library/csv.html
        """
        # csv.py doesn't do Unicode; encode temporarily as UTF-8:
        csv_reader = csv.reader(self._utf_8_encoder(unicode_csv_data),
                                dialect=dialect, **kwargs)
        for row in csv_reader:
            # decode UTF-8 back to Unicode, cell by cell:
            yield [unicode(cell, 'utf-8') for cell in row]

    def _utf_8_encoder(self, unicode_csv_data):
        """
        Yield CSV lines as UTF-8 encoded strings; see https://docs.python.org/2/library/csv.html
        """
        for line in unicode_csv_data:
            yield line.encode('utf-8')
