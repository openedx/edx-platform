/* When the user clicks on the button, 
toggle between hiding and showing the dropdown content */
function dropupError() {
	const dropupElement = document.getElementById("dropupError")
	dropupElement.classList.toggle("show");

	if (dropupElement.classList.contains("show")) {
		const btnSubmit = document.getElementById('submit-feedback')
		const comment = document.getElementById('comment')
		btnSubmit.setAttribute('disabled', 'disabled');
		comment.addEventListener('input', (e)=>{
			if (e.target.value.length > 0){
				btnSubmit.removeAttribute('disabled')
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





const handlerSubmit  = (event)=>{
	event.preventDefault()
	const categoryFeedback = document.getElementById('feedback-category').value;
	const comment = document.getElementById('comment').value
	const fileInput = document.getElementById('fileInput');
	const selectedFile = fileInput.files[0];
	console.log(selectedFile)
	if (selectedFile) {
		const formData = new FormData();
		formData.append('file', selectedFile);
	
	}

}