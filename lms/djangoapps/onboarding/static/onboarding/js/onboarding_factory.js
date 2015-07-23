;(function (define) {
    'use strict';

    define(['jquery', 'backbone', 'onboarding/js/views/onboarding',
            'onboarding/js/collections/course_info'],
        function ($, Backbone, OnboardingView, CourseInfoCollection) {
            return function (options) {
                var courses = new CourseInfoCollection([], {
                    url: options.discoveryUrl,
                    per_page: 9
                }).bootstrap();
                courses.setPage(1).done(function() {
                    var view = new OnboardingView(_.extend(options, {
                        collection: courses,
                        el: $('.onboarding')
                    }));
                    view.render();
                });
                Backbone.history.start();
            };
        });
}).call(this, define || RequireJS.define);
