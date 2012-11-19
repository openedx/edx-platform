CMS.Models.Settings.CourseDetails = Backbone.Models.extend({
	defaults: {
		location : null,	# a Location model, required
		start_date: null,
		end_date: null,
		milestones: null,   # a CourseRelativeCollection
		syllabus: null,
		overview: "",
		statement: "",
		intro_video: null,
		requirements: "",
		effort: null,	# an int or null
		textbooks: null,	# a CourseRelativeCollection
		prereqs: null, 	# a CourseRelativeCollection
		faqs: null 	# a CourseRelativeCollection
	},
	
	// When init'g from html script, ensure you pass {parse: true} as an option (2nd arg to reset)
	parse: function(attributes) {
		if (attributes['location']) {
			attributes.location = new CMS.Models.Location(attributes.location);
		};
		if (attributes['milestones']) {
			attributes.milestones = new CMS.Models.CourseRelativeCollection(attributes.milestones);
		};
		if (attributes['textbooks']) {
			attributes.textbooks = new CMS.Models.CourseRelativeCollection(attributes.textbooks);
		};
		if (attributes['prereqs']) {
			attributes.prereqs = new CMS.Models.CourseRelativeCollection(attributes.prereqs);
		};
		if (attributes['faqs']) {
			attributes.faqs = new CMS.Models.CourseRelativeCollection(attributes.faqs);
		};
	},
	
	urlRoot: function() {
		// TODO impl
	}
});
