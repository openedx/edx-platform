define(["backbone", "js/models/location", "js/collections/course_grader"],
    function(Backbone, Location, CourseGraderCollection) {

var CourseGradingPolicy = Backbone.Model.extend({
    defaults : {
        course_location : null,
        graders : null,  // CourseGraderCollection
        grade_cutoffs : null,  // CourseGradeCutoff model
        grace_period : null // either null or { hours: n, minutes: m, ...}
    },
    parse: function(attributes) {
        if (attributes['course_location']) {
            attributes.course_location = new Location(attributes.course_location, {parse:true});
        }
        if (attributes['graders']) {
            var graderCollection;
            // interesting race condition: if {parse:true} when newing, then parse called before .attributes created
            if (this.attributes && this.has('graders')) {
                graderCollection = this.get('graders');
                graderCollection.reset(attributes.graders);
            }
            else {
                graderCollection = new CourseGraderCollection(attributes.graders);
                graderCollection.course_location = attributes['course_location'] || this.get('course_location');
            }
            attributes.graders = graderCollection;
        }
        // If grace period is unset or equal to 00:00 on the server,
        // it's received as null
        if (attributes['grace_period'] === null) {
            attributes.grace_period = {
                hours: 0,
                minutes: 0
            }
        }
        return attributes;
    },
    url : function() {
        var location = this.get('course_location');
        return '/' + location.get('org') + "/" + location.get('course') + '/settings-details/' + location.get('name') + '/section/grading';
    },
    gracePeriodToDate : function() {
        var newDate = new Date();
        if (this.has('grace_period') && this.get('grace_period')['hours'])
            newDate.setHours(this.get('grace_period')['hours']);
        else newDate.setHours(0);
        if (this.has('grace_period') && this.get('grace_period')['minutes'])
            newDate.setMinutes(this.get('grace_period')['minutes']);
        else newDate.setMinutes(0);
        if (this.has('grace_period') && this.get('grace_period')['seconds'])
            newDate.setSeconds(this.get('grace_period')['seconds']);
        else newDate.setSeconds(0);

        return newDate;
    },
    parseGracePeriod : function(grace_period) {
        // Enforce hours:minutes format
        if(!/^\d{2,3}:\d{2}$/.test(grace_period)) {
            return null;
        }
        var pieces = grace_period.split(/:/);
        return {
            hours: parseInt(pieces[0], 10),
            minutes: parseInt(pieces[1], 10)
        }
    },
    validate : function(attrs) {
        if(_.has(attrs, 'grace_period')) {
            if(attrs['grace_period'] === null) {
                return {
                    'grace_period': gettext('Grace period must be specified in HH:MM format.')
                }
            }
        }
    }
});

return CourseGradingPolicy;
}); // end define()
