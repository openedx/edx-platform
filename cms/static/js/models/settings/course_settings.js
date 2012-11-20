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
	},

	retrieve: function(submodel, callback) {
		if (this.get(submodel)) callback();
		else switch (submodel) {
		case 'details':
			this.set('details', new CMS.Models.Settings.CourseDetails({location: this.get('courseLocation')})).fetch({
				success : callback
			});
			break;

		default:
			break;
		}
	}
})