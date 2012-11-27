if (!CMS.Models['Settings']) CMS.Models.Settings = new Object();

CMS.Models.Settings.CourseDetails = Backbone.Model.extend({
	defaults: {
		location : null,	// the course's Location model, required
		start_date: null,	// maps to 'start'
		end_date: null,		// maps to 'end'
		enrollment_start: null,
		enrollment_end: null,
		syllabus: null,
		overview: "",
		intro_video: null,
		effort: null	// an int or null
	},
	
	// When init'g from html script, ensure you pass {parse: true} as an option (2nd arg to reset)
	parse: function(attributes) {
		if (attributes['course_location']) {
			attributes.location = new CMS.Models.Location(attributes.course_location, {parse:true});
		}
		if (attributes['start_date']) {
			attributes.start_date = new Date(attributes.start_date);
		}
		if (attributes['end_date']) {
			attributes.end_date = new Date(attributes.end_date);
		}
		if (attributes['enrollment_start']) {
			attributes.enrollment_start = new Date(attributes.enrollment_start);
		}
		if (attributes['enrollment_end']) {
			attributes.enrollment_end = new Date(attributes.enrollment_end);
		}
		return attributes;
	},
	
	urlRoot: function() {
		var location = this.get('location');
		return '/' + location.get('org') + "/" + location.get('course') + '/settings/' + location.get('name') + '/section/details';
	}
});
