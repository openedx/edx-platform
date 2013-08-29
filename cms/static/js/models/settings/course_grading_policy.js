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
        if (_.has(attrs, 'type')) {
            if (_.isEmpty(attrs['type'])) {
                errors.type = "The assignment type must have a name.";
            }
            else {
                // FIXME somehow this.collection is unbound sometimes. I can't track down when
                var existing = this.collection && this.collection.some(function(other) { return (other.cid != this.cid) && (other.get('type') == attrs['type']);}, this);
                if (existing) {
                    errors.type = gettext("There's already another assignment type with this name.");
                }
            }
        }
        if (_.has(attrs, 'weight')) {
            var intWeight = parseInt(attrs.weight); // see if this ensures value saved is int
            if (!isFinite(intWeight) || /\D+/.test(attrs.weight) || intWeight < 0 || intWeight > 100) {
                errors.weight = gettext("Please enter an integer between 0 and 100.");
            }
            else {
                attrs.weight = intWeight;
                if (this.collection && attrs.weight > 0) {
                    // FIXME b/c saves don't update the models if validation fails, we should
                    // either revert the field value to the one in the model and make them make room
                    // or figure out a wholistic way to balance the vals across the whole
//                  if ((this.collection.sumWeights() + attrs.weight - this.get('weight')) > 100)
//                  errors.weight = "The weights cannot add to more than 100.";
                }
            }}
        if (_.has(attrs, 'min_count')) {
            if (!isFinite(attrs.min_count) || /\D+/.test(attrs.min_count)) {
                errors.min_count = gettext("Please enter an integer.");
            }
            else attrs.min_count = parseInt(attrs.min_count);
        }
        if (_.has(attrs, 'drop_count')) {
            if (!isFinite(attrs.drop_count) || /\D+/.test(attrs.drop_count)) {
                errors.drop_count = gettext("Please enter an integer.");
            }
            else attrs.drop_count = parseInt(attrs.drop_count);
        }
        if (_.has(attrs, 'min_count') && _.has(attrs, 'drop_count') && attrs.drop_count > attrs.min_count) {
            errors.drop_count = _.template(
                gettext("Cannot drop more <% attrs.types %> than will assigned."),
                attrs, {variable: 'attrs'});
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
