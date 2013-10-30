define(["backbone"], function(Backbone) {
    var CourseRelative = Backbone.Model.extend({
        defaults: {
            course_location : null, // must never be null, but here to doc the field
            idx : null  // the index making it unique in the containing collection (no implied sort)
        }
    });
    return CourseRelative;
});
