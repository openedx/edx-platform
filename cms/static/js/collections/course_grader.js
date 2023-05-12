// eslint-disable-next-line no-undef
define(['backbone', 'js/models/settings/course_grader'], function(Backbone, CourseGrader) {
    // eslint-disable-next-line no-var
    var CourseGraderCollection = Backbone.Collection.extend({
        model: CourseGrader,
        sumWeights: function() {
            return this.reduce(function(subtotal, grader) { return subtotal + grader.get('weight'); }, 0);
        }
    });

    return CourseGraderCollection;
}); // end define()
