CMS.Models.Settings.CourseSettings = Backbone.Model.extend({
	// a container for the models representing the n possible tabbed states
	defaults: {
		courseLocation: null,
		// NOTE: keep these sync'd w/ the data-section names in settings-page-menu
		details: null,
		faculty: null,
		grading: null,
		problems: null,
		discussions: null
	}
	// write getters which get the relevant sub model from the server if not already loaded
})