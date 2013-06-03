if (!CMS.Models['Settings']) CMS.Models.Settings = new Object();

CMS.Models.Settings.CourseGradingPolicy = Backbone.Model.extend({
    defaults : {
        course_location : null,
        graders : null,  // CourseGraderCollection
        grade_cutoffs : null,  // CourseGradeCutoff model
        grace_period : null // either null or { hours: n, minutes: m, ...}
    },
    parse: function(attributes) {
        if (attributes['course_location']) {
            attributes.course_location = new CMS.Models.Location(attributes.course_location, {parse:true});
        }
        if (attributes['graders']) {
            var graderCollection;
            // interesting race condition: if {parse:true} when newing, then parse called before .attributes created
            if (this.attributes && this.has('graders')) {
                graderCollection = this.get('graders');
                graderCollection.reset(attributes.graders);
            }
            else {
                graderCollection = new CMS.Models.Settings.CourseGraderCollection(attributes.graders);
                graderCollection.course_location = attributes['course_location'] || this.get('course_location');
            }
            attributes.graders = graderCollection;
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
    dateToGracePeriod : function(date) {
        return {hours : date.getHours(), minutes : date.getMinutes(), seconds : date.getSeconds() };
    }
});

CMS.Models.Settings.CourseGrader = Backbone.Model.extend({
    defaults: {
        "type" : "",	// must be unique w/in collection (ie. w/in course)
        "min_count" : 1,
        "drop_count" : 0,
        "short_label" : "",	// what to use in place of type if space is an issue
        "weight" : 0 // int 0..100
    },
    parse : function(attrs) {
        if (attrs['weight']) {
            if (!_.isNumber(attrs.weight)) attrs.weight = parseInt(attrs.weight);
        }
        if (attrs['min_count']) {
            if (!_.isNumber(attrs.min_count)) attrs.min_count = parseInt(attrs.min_count);
        }
        if (attrs['drop_count']) {
            if (!_.isNumber(attrs.drop_count)) attrs.drop_count = parseInt(attrs.drop_count);
        }
        return attrs;
    },
    validate : function(attrs) {
        var errors = {};
        if (attrs['type']) {
            if (_.isEmpty(attrs['type'])) {
                errors.type = "The assignment type must have a name.";
            }
            else {
                // FIXME somehow this.collection is unbound sometimes. I can't track down when
                var existing = this.collection && this.collection.some(function(other) { return (other != this) && (other.get('type') == attrs['type']);}, this);
                if (existing) {
                    errors.type = "There's already another assignment type with this name.";
                }
            }
        }
        if (attrs['weight']) {
            if (!isFinite(attrs.weight) || /\D+/.test(attrs.weight)) {
                errors.weight = "Please enter an integer between 0 and 100.";
            }
            else {
                attrs.weight = parseInt(attrs.weight); // see if this ensures value saved is int
                if (this.collection && attrs.weight > 0) {
                    // FIXME b/c saves don't update the models if validation fails, we should
                    // either revert the field value to the one in the model and make them make room
                    // or figure out a wholistic way to balance the vals across the whole
//                  if ((this.collection.sumWeights() + attrs.weight - this.get('weight')) > 100)
//                  errors.weight = "The weights cannot add to more than 100.";
                }
            }}
        if (attrs['min_count']) {
            if (!isFinite(attrs.min_count) || /\D+/.test(attrs.min_count)) {
                errors.min_count = "Please enter an integer.";
            }
            else attrs.min_count = parseInt(attrs.min_count);
        }
        if (attrs['drop_count']) {
            if (!isFinite(attrs.drop_count) || /\D+/.test(attrs.drop_count)) {
                errors.drop_count = "Please enter an integer.";
            }
            else attrs.drop_count = parseInt(attrs.drop_count);
        }
        if (attrs['min_count'] && attrs['drop_count'] && attrs.drop_count > attrs.min_count) {
            errors.drop_count = "Cannot drop more " + attrs.type + " than will assigned.";
        }
        if (!_.isEmpty(errors)) return errors;
    }
});

CMS.Models.Settings.CourseGraderCollection = Backbone.Collection.extend({
    model : CMS.Models.Settings.CourseGrader,
    course_location : null, // must be set to a Location object
    url : function() {
        return '/' + this.course_location.get('org') + "/" + this.course_location.get('course') + '/settings-grading/' + this.course_location.get('name') + '/';
    },
    sumWeights : function() {
        return this.reduce(function(subtotal, grader) { return subtotal + grader.get('weight'); }, 0);
    }
});
