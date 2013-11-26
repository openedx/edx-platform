define(["backbone", "js/models/course_relative"], function(Backbone, CourseRelativeModel) {
    var CourseRelativeCollection = Backbone.Collection.extend({
        model: CourseRelativeModel
    });
    return CourseRelativeCollection;
});
