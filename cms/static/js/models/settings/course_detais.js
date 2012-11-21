CMS.Models.Settings.CourseDetails = Backbone.Models.extend({
	defaults: {
		location : null,	// the course's Location model, required
		start_date: null,	// maps to 'start'
		end_date: null,		// maps to 'end'
		enrollment_start: null,
		enrollment_end: null,
		syllabus: null,
		overview: "",
		intro_video: null,
		effort: null	# an int or null
	},
	
	// When init'g from html script, ensure you pass {parse: true} as an option (2nd arg to reset)
	parse: function(attributes) {
		if (attributes['location']) {
			attributes.location = new CMS.Models.Location(attributes.location);
		};
	},
	
	urlRoot: function() {
		var location = this.get('location');
		return '/' + location.get('org') + "/" + location.get('course') + '/settings/' + location.get('name') + '/section/details';
	}
});
