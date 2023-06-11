/* When the user clicks on the button, 
toggle between hiding and showing the dropdown content */
function dropupError() {
	document.getElementById("dropupError").classList.toggle("show");
}

// Technical Error
function openTechError() {
	document.getElementById("technicalError").classList.toggle("show");
	document.getElementById("dropupError").classList.toggle("show");
}

function closeTechError() {
	document.getElementById("technicalError").classList.toggle("show");
}

//Overall Content Error
function openOverallError() {
	document.getElementById("overallError").classList.toggle("show");
	document.getElementById("dropupError").classList.toggle("show");
}

function closeOverallError() {
	document.getElementById("overallError").classList.toggle("show");
}

//Quiz Content Error
function openQuizError() {
	document.getElementById("quizError").classList.toggle("show");
	document.getElementById("dropupError").classList.toggle("show");
}

function closeQuizError() {
	document.getElementById("quizError").classList.toggle("show");
}

//Ask Mentor Error
function openMentorError() {
	document.getElementById("mentorError").classList.toggle("show");
	document.getElementById("dropupError").classList.toggle("show");
}

function closeMentorError() {
	document.getElementById("mentorError").classList.toggle("show");
}

function postFeedback(e, form, closeClass) {
	e.preventDefault()

	// Popolate hidden values
	populateForm();


	// Change loading icon
	$(".btnSend").html('<i class="fa fa-refresh fa-spin fa-fw"></i>');

	let url = this.LMSHost + "/feedback/";
	let formData = new FormData(form);
	let xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function () {
	if (this.readyState == 4 && this.status == 200) {
		if (this.responseText == "success") {
			// Hide the feedback form
			$(".btnSend").html('Gửi');
			$('textarea[name="content"]').val('');
			$('input[name="attachment"]').val('');
			$('.' + closeClass).click();

			alert('Cám ơn bạn đã gửi phản hồi lỗi!');
		} else {
			$(".btnSend").html('Gửi');
			alert('Xin lỗi hiện hệ thống đang chưa gửi được phản hồi. Xin bạn vui lòng báo lại hannah nhé!');
		}
	}
	};
	xhttp.open("POST", url, true);
	xhttp.send(formData);
}

function populateForm() {
	let url = window.location;
	$("input[name='lesson_url']").val(url);

	let patt = new RegExp("[+].*[+]");
	let res = patt.exec(url);
	if (res) {
		let instance_code = res[0].substring(1, res[0].length - 1);
		$("input[name='instance_code']").val(instance_code);
		} else {
		$("input[name='instance_code']").val('N/A');
	}

	let title = $("div.xblock-student_view h2.unit-title");
	if (title && title.text() != '') { // Check if in a course lesson
		let unit_title = title.text();
		$("input[name='unit_title']").val(unit_title);
	} else {
		$("input[name='unit_title']").val('N/A');
	}
}

const addFeedbackForm = async () => {
	// Get form html form api and append to body using fetch
	let url = this.LMSHost + '/feedback';
	await fetch(url)
		.then(response => response.text())
		.then(html => {
			document.body.insertAdjacentHTML('beforeend', html);
		});

	document.getElementById("technical_error_form").onsubmit = function (e) {
		postFeedback(e, this, 'btn-technical')
	};
	document.getElementById("content_error_form").onsubmit = function (e) {
		postFeedback(e, this, 'btn-content')
	};
	document.getElementById("quiz_error_form").onsubmit = function (e) {
		postFeedback(e, this, 'btn-quiz')
	};
}

const initFUNiXFeedback = (LMSHost = '') => {	
	this.LMSHost = LMSHost;

	addFeedbackForm()
};