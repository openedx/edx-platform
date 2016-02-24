define(["backbone", "underscore", "gettext", "js/models/validation_helpers", "js/utils/date_utils"],
    function(Backbone, _, gettext, ValidationHelpers, DateUtils) {

var CourseDetails = Backbone.Model.extend({
    defaults: {
        language: '',
        short_description: "",
        overview: "",
        intro_video: null,
        course_image_name: '', // the filename
        course_image_asset_path: '', // the full URL (/c4x/org/course/num/asset/filename)
    },

    validate: function(newattrs) {
        // Returns either nothing (no return call) so that validate works or an object of {field: errorstring} pairs
        // A bit funny in that the video key validation is asynchronous; so, it won't stop the validation.
        var errors = {};
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
    },

    // Whether or not the course pacing can be toggled. If the course
    // has already started, returns false; otherwise, returns true.
    canTogglePace: function () {
        return new Date() <= new Date(this.get('start_date'));
    }
});

return CourseDetails;

}); // end define()
