define(["backbone", "underscore", "gettext"], function(Backbone, _, gettext) {

var CourseDetails = Backbone.Model.extend({
    defaults: {
        org : '',
        course_id: '',
        run: '',
        start_date: null,	// maps to 'start'
        end_date: null,		// maps to 'end'
        enrollment_start: null,
        enrollment_end: null,
        syllabus: null,
        short_description: "",
        overview: "",
        intro_video: null,
        effort: null,	// an int or null,
        course_image_name: '', // the filename
        course_image_asset_path: '' // the full URL (/c4x/org/course/num/asset/filename)
    },

    // When init'g from html script, ensure you pass {parse: true} as an option (2nd arg to reset)
    parse: function(attributes) {
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

    validate: function(newattrs) {
        // Returns either nothing (no return call) so that validate works or an object of {field: errorstring} pairs
        // A bit funny in that the video key validation is asynchronous; so, it won't stop the validation.
        var errors = {};
        if (newattrs.start_date === null) {
            errors.start_date = gettext("The course must have an assigned start date.");
        }
        if (newattrs.start_date && newattrs.end_date && newattrs.start_date >= newattrs.end_date) {
            errors.end_date = gettext("The course end date cannot be before the course start date.");
        }
        if (newattrs.start_date && newattrs.enrollment_start && newattrs.start_date < newattrs.enrollment_start) {
            errors.enrollment_start = gettext("The course start date cannot be before the enrollment start date.");
        }
        if (newattrs.enrollment_start && newattrs.enrollment_end && newattrs.enrollment_start >= newattrs.enrollment_end) {
            errors.enrollment_end = gettext("The enrollment start date cannot be after the enrollment end date.");
        }
        if (newattrs.end_date && newattrs.enrollment_end && newattrs.end_date < newattrs.enrollment_end) {
            errors.enrollment_end = gettext("The enrollment end date cannot be after the course end date.");
        }
        if (newattrs.intro_video && newattrs.intro_video !== this.get('intro_video')) {
            if (this._videokey_illegal_chars.exec(newattrs.intro_video)) {
                errors.intro_video = gettext("Key should only contain letters, numbers, _, or -");
            }
            // TODO check if key points to a real video using google's youtube api
        }
        if (!_.isEmpty(errors)) return errors;
        // NOTE don't return empty errors as that will be interpreted as an error state
    },

    _videokey_illegal_chars : /[^a-zA-Z0-9_-]/g,
    set_videosource: function(newsource) {
        // newsource either is <video youtube="speed:key, *"/> or just the "speed:key, *" string
        // returns the videosource for the preview which iss the key whose speed is closest to 1
        if (_.isEmpty(newsource) && !_.isEmpty(this.get('intro_video'))) this.set({'intro_video': null}, {validate: true});
        // TODO remove all whitespace w/in string
        else {
            if (this.get('intro_video') !== newsource) this.set('intro_video', newsource, {validate: true});
        }

        return this.videosourceSample();
    },
    videosourceSample : function() {
        if (this.has('intro_video')) return "//www.youtube.com/embed/" + this.get('intro_video');
        else return "";
    }
});

return CourseDetails;

}); // end define()
