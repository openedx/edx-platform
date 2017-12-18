(function(define) {
    'use strict';
    define([
        'backbone',
        'js/learner_dashboard/models/course_card_model'
    ],
    function(Backbone, CourseCard) {
        return Backbone.Collection.extend({
            model: CourseCard
        });
    });
}).call(this, define || RequireJS.define);
