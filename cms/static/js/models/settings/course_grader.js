define(["backbone", "underscore", "gettext"], function(Backbone, _, gettext) {

var CourseGrader = Backbone.Model.extend({
    defaults: {
        "type" : "",    // must be unique w/in collection (ie. w/in course)
        "min_count" : 1,
        "drop_count" : 0,
        "short_label" : "", // what to use in place of type if space is an issue
        "weight" : 0 // int 0..100
    },
    parse : function(attrs) {
        if (attrs['weight']) {
            if (!_.isNumber(attrs.weight)) attrs.weight = parseInt(attrs.weight, 10);
        }
        if (attrs['min_count']) {
            if (!_.isNumber(attrs.min_count)) attrs.min_count = parseInt(attrs.min_count, 10);
        }
        if (attrs['drop_count']) {
            if (!_.isNumber(attrs.drop_count)) attrs.drop_count = parseInt(attrs.drop_count, 10);
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
                    // or figure out a holistic way to balance the vals across the whole
//                  if ((this.collection.sumWeights() + attrs.weight - this.get('weight')) > 100)
//                  errors.weight = "The weights cannot add to more than 100.";
                }
            }}
        if (_.has(attrs, 'min_count')) {
            if (!isFinite(attrs.min_count) || /\D+/.test(attrs.min_count)) {
                errors.min_count = gettext("Please enter an integer.");
            }
            else attrs.min_count = parseInt(attrs.min_count, 10);
        }
        if (_.has(attrs, 'drop_count')) {
            if (!isFinite(attrs.drop_count) || /\D+/.test(attrs.drop_count)) {
                errors.drop_count = gettext("Please enter an integer.");
            }
            else attrs.drop_count = parseInt(attrs.drop_count, 10);
        }
        if (_.has(attrs, 'min_count') && _.has(attrs, 'drop_count') && attrs.drop_count > attrs.min_count) {
            errors.drop_count = _.template(
                gettext("Cannot drop more <% attrs.types %> than will assigned."),
                attrs, {variable: 'attrs'});
        }
        if (!_.isEmpty(errors)) return errors;
    }
});

return CourseGrader;
}); // end define()
