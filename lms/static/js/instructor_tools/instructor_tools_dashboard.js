(function() {
    'use strict';
  	// eslint-disable-next-line no-unused-vars

	const GradeAPI = '/instructor_tools/api/calculate_all_grades_csv'

	$(document).ready(function() {
		const $gradeReportDownload = $('.grade-report-download');
		$gradeReportDownload.click(function(e) {
			$.post(GradeAPI, (res) => {
				console.log(res)
			})
		})
    });
}).call(this);