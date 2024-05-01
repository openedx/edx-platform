(function(define) {
    define([
        'jquery',
        'underscore',
        'backbone',
        'gettext',
        'js/discovery/views/course_card',
        'edx-ui-toolkit/js/utils/html-utils'
    ], function($, _, Backbone, gettext, CourseCardView, HtmlUtils) {
        'use strict';

        return Backbone.View.extend({

            el: 'div.courses',
            $window: $(window),
            $document: $(document),

            initialize: function() {
                this.$currentCoursesList = this.$el.find('.current-courses-listing');
                this.$upcomingCoursesList = this.$el.find('.upcoming-courses-listing');
                this.$selfPacedCoursesList = this.$el.find('.self-paced-courses-listing');
                this.$pastCoursesList = this.$el.find('.past-courses-listing');
                this.attachScrollHandler();
            },

            render: function() {
                this.$currentCoursesList.empty();
                this.$upcomingCoursesList.empty();
                this.$selfPacedCoursesList.empty();
                this.$pastCoursesList.empty();
                this.renderItems();
                return this;
            },

            renderNext: function() {
                this.renderItems();
                this.isLoading = false;
            },

            sortCurrentCourses: function(course1, course2) {
                var date1 = new Date(course1.attributes.end);
                var date2 = new Date(course2.attributes.end);
                return date1.getTime() - date2.getTime()
            },

            renderItems: function() {
                /* eslint no-param-reassign: [2, { "props": true }] */
                var latest = this.model.latest();
                var currentDate = new Date();
                var currentCourses = [];
                var upcomingCourses = [];
                var selfPacedCourses = [];
                var pastCourses = [];

                for (var i = 0; i < latest.length; i++) {
                    var course = latest[i];
                    if (course.attributes.self_paced) {
                        selfPacedCourses.push(course);
                    } else {
                        var course_start = new Date(course.attributes.start);
                        var course_end = new Date(course.attributes.end);
                        if (course_start <= currentDate && course_end >= currentDate) {
                            currentCourses.push(course);
                        } else if (course_start > currentDate && course_end > currentDate) {
                            upcomingCourses.push(course);
                        } else if (course_start < currentDate && course_end < currentDate) {
                            pastCourses.push(course);
                        }
                    }
                }

                currentCourses.sort(this.sortCurrentCourses);

                var currentCoursesItems = currentCourses.map(function(result) {
                    result.userPreferences = this.model.userPreferences;
                    var item = new CourseCardView({model: result});
                    return item.render().el;
                }, this);

                var upcomingCoursesItems = upcomingCourses.map(function(result) {
                    result.userPreferences = this.model.userPreferences;
                    var item = new CourseCardView({model: result});
                    return item.render().el;
                }, this);

                var selfPacedCoursesItems = selfPacedCourses.map(function(result) {
                    result.userPreferences = this.model.userPreferences;
                    var item = new CourseCardView({model: result});
                    return item.render().el;
                }, this);

                var pastCoursesItems = pastCourses.map(function(result) {
                    result.userPreferences = this.model.userPreferences;
                    var item = new CourseCardView({model: result});
                    return item.render().el;
                }, this);

                if (currentCourses.length) {
                    HtmlUtils.append(
                        this.$currentCoursesList,
                        HtmlUtils.HTML(currentCoursesItems)
                    );
                    if ($(".current-courses-header").length === 0) {
                        this.$currentCoursesList.before("<h2 class='current-courses-header'>Current courses</h2>");
                    }
                } else {
                    if ($(".current-courses-header").length === 1) {
                        $(".current-courses-header").remove();
                    }
                }

                if (upcomingCourses.length) {
                    HtmlUtils.append(
                        this.$upcomingCoursesList,
                        HtmlUtils.HTML(upcomingCoursesItems)
                    );
                    if ($(".upcoming-courses-header").length === 0) {
                        this.$upcomingCoursesList.before("<h2 class='upcoming-courses-header'>Upcoming courses</h2>");
                    }
                } else {
                    if ($(".upcoming-courses-header").length === 1) {
                        $(".upcoming-courses-header").remove();
                    }
                }

                if (selfPacedCourses.length) {
                    HtmlUtils.append(
                        this.$selfPacedCoursesList,
                        HtmlUtils.HTML(selfPacedCoursesItems)
                    );
                    if ($(".self-paced-courses-header").length === 0) {
                        this.$selfPacedCoursesList.before("<h2 class='self-paced-courses-header'>Self paced courses</h2>");
                    }
                } else {
                    if ($(".self-paced-courses-header").length === 1) {
                        $(".self-paced-courses-header").remove();
                    }
                }

                if (pastCourses.length) {
                    HtmlUtils.append(
                        this.$pastCoursesList,
                        HtmlUtils.HTML(pastCoursesItems)
                    );
                    if ($(".past-courses-header").length === 0) {
                        this.$pastCoursesList.before("<h2 class='past-courses-header'>Past courses</h2>");
                    }
                } else {
                    if ($(".past-courses-header").length === 1) {
                        $(".past-courses-header").remove();
                    }
                }

                /* eslint no-param-reassign: [2, { "props": false }] */
            },

            attachScrollHandler: function() {
                this.$window.on('scroll', _.throttle(this.scrollHandler.bind(this), 400));
            },

            scrollHandler: function() {
                if (this.isNearBottom() && !this.isLoading) {
                    this.trigger('next');
                    this.isLoading = true;
                }
            },

            isNearBottom: function() {
                var scrollBottom = this.$window.scrollTop() + this.$window.height();
                var threshold = this.$document.height() - 200;
                return scrollBottom >= threshold;
            }

        });
    });
}(define || RequireJS.define));
