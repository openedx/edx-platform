/**
 * View that displays a card for a course.
 */
;(function (define) {
    'use strict';
    define(['backbone', 'underscore', 'text!onboarding/templates/course-card.underscore'],
        function (Backbone, _, course_card_template) {
            var CourseCardView = Backbone.View.extend({

                className: "card square-card",

                render: function() {
                    this.$el.html(_.template(course_card_template, {
                        title: this.model.get('name'),
                        description: '',
                        image_url: this.model.get('image_url'),
                        course_url: this.getCourseUrl()
                    }));
                    return this;
                },

                getCourseUrl: function() {
                    return '/onboarding/course/' + this.model.get('org') + '/' +
                        this.model.get('course') + '/' +
                        this.model.get('run');
                }
            });

            return CourseCardView;
        });
}).call(this, define || RequireJS.define);
