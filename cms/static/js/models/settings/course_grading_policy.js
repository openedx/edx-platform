define(["backbone", "js/models/location", "js/collections/course_grader"],
    function(Backbone, Location, CourseGraderCollection) {

var CourseGradingPolicy = Backbone.Model.extend({
    defaults : {
        graders : null,  // CourseGraderCollection
        grade_cutoffs : null,  // CourseGradeCutoff model
        grace_period : null, // either null or { hours: n, minutes: m, ...}
        minimum_grade_credit : null, // either null or percentage
        minimum_grade_verified_certificate : null // either null or percentage
    },
    parse: function(attributes) {
        if (attributes['graders']) {
            var graderCollection;
            // interesting race condition: if {parse:true} when newing, then parse called before .attributes created
            if (this.attributes && this.has('graders')) {
                graderCollection = this.get('graders');
                graderCollection.reset(attributes.graders, {parse:true});
            }
            else {
                graderCollection = new CourseGraderCollection(attributes.graders, {parse:true});
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
        // If minimum_grade_credit is unset or equal to 0 on the server,
        // it's received as 0
        if (attributes.minimum_grade_credit === null) {
            attributes.minimum_grade_credit = 0;
        }
        return attributes;
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
    parseMinimumGradeCredit : function(minimum_grade_credit) {
        // get the value of minimum grade credit value in percentage
        if (isNaN(minimum_grade_credit)) {
            return 0;
        }
        return parseInt(minimum_grade_credit);
    },
    parseMinimumGradeVerifiedCertificate : function(minimum_grade_verified_certificate) {
        // get the value of minimum grade verified certificate value in percentage
        var value = parseFloat(minimum_grade_verified_certificate);
        if (isNaN(value)) {
            return null;
        } else {
            return value / 100;
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
        if(this.get('is_credit_course') && _.has(attrs, 'minimum_grade_credit')) {
            // Getting minimum grade cutoff value
            var minimum_grade_cutoff = _.min(_.values(attrs.grade_cutoffs));
            if(isNaN(attrs.minimum_grade_credit) || attrs.minimum_grade_credit === null || attrs.minimum_grade_credit < minimum_grade_cutoff) {
                return {
                    'minimum_grade_credit': interpolate(
                        gettext('Not able to set passing grade to less than %(minimum_grade_cutoff)s%.'),
                        {minimum_grade_cutoff: minimum_grade_cutoff * 100},
                        true
                    )
                };
            }
        }
    }
});

return CourseGradingPolicy;
}); // end define()
