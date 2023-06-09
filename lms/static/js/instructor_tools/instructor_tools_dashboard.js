(function () {
	'use strict';
	// eslint-disable-next-line no-unused-vars

	const GradeAPI = '/instructor_tools/api/calculate_all_grades_csv'

	$(document).ready(function () {
		const $gradeReportDownload = $('.grade-report-download');
		$gradeReportDownload.click(function (e) {
			// Show loading spinner by Swal
			Swal.fire({
				title: 'Generating...',
				html: 'Generating all grade csv file!',
				allowOutsideClick: false,
				didOpen: () => {
					Swal.showLoading()
				},
			});

			$.post(GradeAPI, (res) => {
				// Get output and redirect to download
				const {
					output
				} = res;
				if (output) {
					// Get file name from output path
					const fileName = output.split('/').pop();

					// Go to link in new tab
					window.open('http://localhost:18000/media/' + fileName, '_blank');
				} else {
					Swal.fire({
					title: 'Error',
					text: 'Something went wrong!',
					icon: 'error',
					});
				}

				// Close the Swal
				Swal.close();
			})
		})
	});
}).call(this);