CMS.ServerError = function(model, error) {
	// this handler is for the client:server communication not the validation errors which handleValidationError catches
	window.alert("Server Error: " + error.responseText);
};