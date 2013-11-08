define(["backbone", "js/models/settings/course_grader"], function(Backbone, CourseGrader) {

var CourseGraderCollection = Backbone.Collection.extend({
    model : CourseGrader,
    course_location : null, // must be set to a Location object
    url : function() {
        return '/' + this.course_location.get('org') + "/" + this.course_location.get('course') + '/settings-grading/' + this.course_location.get('name') + '/';
    },
    sumWeights : function() {
        return this.reduce(function(subtotal, grader) { return subtotal + grader.get('weight'); }, 0);
    }
});

return CourseGraderCollection;
}); // end define()
