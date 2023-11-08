/* When the user clicks on the button, 
toggle between hiding and showing the dropdown content */
function dropupError() {
	const dropupElement = document.getElementById("dropupError")
	dropupElement.classList.toggle("show");

	if (dropupElement.classList.contains("show")) {
		const btnSubmit = document.getElementById('submit-feedback')
		const comment = document.getElementById('comments')
		btnSubmit.setAttribute('disabled', 'disabled');
		comment.addEventListener('input', (e)=>{
			if (e.target.value.length > 0){
				btnSubmit.removeAttribute('disabled')
			}else {
				btnSubmit.setAttribute('disabled', 'disabled');
			}
		})
	  } 
}




const addFeedbackForm = async () => {
	// Get form html form api and append to body using fetch
	let url = this.LMSHost + '/feedback/';
	await fetch(url, {
		method: "GET",
		headers: {},
		credentials: 'include'
	})
	.then(response => response.text())
	.then(html => {
		document.body.insertAdjacentHTML('beforeend', html);
	});

	
}

const initFUNiXFeedback = (LMSHost = '', isMFE = false) => {	
	this.LMSHost = LMSHost;
	this.isMFE = isMFE;

	addFeedbackForm()
};



const fetchFeedbackPortal = async (data)=>{
	const datatext = {
		student_email : data.student_email,
		ticket_category : data.ticket_category,
		course_id : 1,
		lesson_url : data.lesson_url,
		image : data.image,
		ticket_description: data.ticket_description
	}
	try {
		const res = await fetch ('http://staging-portal.funix.edu.vn/api/feedback-ticket-management/create' ,
		{
			headers:{"Content-Type": "application/json"},
			method: "POST" ,
			body : JSON.stringify(datatext)
		})
		const data = await res.json()
		console.log(res, data)
	} catch (error) {
		console.log(error)
	}
}


const fetchFeedbackLMS = async (url , formData)=>{
	try {
		const response = await fetch(url, {
		  method: 'POST',
		  headers: {
			'X-CSRFToken': csrf_token
		  },
		  body: formData,
		});
		const data = await response.json();
		console.log('API Response:', data);
		
		return data
	} catch (error) {
		console.error('API Request Error:', error);
	  }
}



const handlerSubmit  = async (event)=>{
	event.preventDefault()
	let url =this.LMSHost + '/api/feedback/create'
	const lesson_url = window.location.href
	const csrf_token = document.getElementById('csrf_token').value
	const feedbackcategory = document.getElementById('feedback-category').value
	const comment = document.getElementById('comments').value
	const email = document.getElementById('email').value
	const formData = new FormData();

	const regex = /course-v1:([^/]+)/;
	const course_id = lesson_url.match(regex)[0]
	// const course_status = course_id.split('+')[1]
	
	formData.append('attachment', fileInput.files[0]);
	formData.append('category_id', feedbackcategory)
	formData.append('content' , comment)
	formData.append('email' , email)
	formData.append('lesson_url' , lesson_url)
	formData.append('course_id', course_id)

	try {
		const data = await fetchFeedbackLMS(url , formData)
		await fetchFeedbackPortal(data)
		document.getElementById('fileInput').value = null;
		document.getElementById('comments').value = '';
		alert('Cám ơn bạn đã gửi phản hồi lỗi!')
	} catch (error) {
		console.log(error)
	}
	


}




