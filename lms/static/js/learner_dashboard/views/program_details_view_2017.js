(function(define) {
    'use strict';
    define(['backbone',
        'jquery',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'js/learner_dashboard/collections/course_card_collection',
        'js/learner_dashboard/views/program_header_view_2017',
        'js/learner_dashboard/views/collection_list_view',
        'js/learner_dashboard/views/course_card_view_2017',
        'js/learner_dashboard/views/program_details_sidebar_view',
        'text!../../../templates/learner_dashboard/program_details_view_2017.underscore'
    ],
         function(
             Backbone,
             $,
             _,
             gettext,
             HtmlUtils,
             CourseCardCollection,
             HeaderView,
             CollectionListView,
             CourseCardView,
             SidebarView,
             pageTpl
         ) {
             return Backbone.View.extend({
                 el: '.js-program-details-wrapper',

                 tpl: HtmlUtils.template(pageTpl),

                 initialize: function(options) {
                     this.options = options;
                     this.programModel = new Backbone.Model(this.options.programData);
                     this.courseData = new Backbone.Model(this.options.courseData);
                     this.completedCourseCollection = new CourseCardCollection(
                        this.courseData.get('completed') || [],
                        this.options.userPreferences
                     );
                     this.inProgressCourseCollection = new CourseCardCollection(
                        this.courseData.get('in_progress') || [],
                        this.options.userPreferences
                     );
                     this.remainingCourseCollection = new CourseCardCollection(
                        this.courseData.get('not_started') || [],
                        this.options.userPreferences
                     );

                     this.render();
                 },

                 render: function() {
                     var completedCount = this.completedCourseCollection.length,
                         inProgressCount = this.inProgressCourseCollection.length,
                         remainingCount = this.remainingCourseCollection.length,
                         totalCount = completedCount + inProgressCount + remainingCount,
                         data = {
                             totalCount: totalCount,
                             inProgressCount: inProgressCount,
                             remainingCount: remainingCount,
                             completedCount: completedCount
                         };
                     data = $.extend(data, this.options.programData);
                     HtmlUtils.setHtml(this.$el, this.tpl(data));
                     this.postRender();
                 },

                 postRender: function() {
                     this.headerView = new HeaderView({
                         model: new Backbone.Model(this.options)
                     });

                     if (this.remainingCourseCollection.length > 0) {
                         new CollectionListView({
                             el: '.js-course-list-remaining',
                             childView: CourseCardView,
                             collection: this.remainingCourseCollection,
                             context: this.options
                         }).render();
                     }

                     if (this.completedCourseCollection.length > 0) {
                         new CollectionListView({
                             el: '.js-course-list-completed',
                             childView: CourseCardView,
                             collection: this.completedCourseCollection,
                             context: this.options
                         }).render();
                     }

                     if (this.inProgressCourseCollection.length > 0) {
                         // This is last because the context is modified below
                         new CollectionListView({
                             el: '.js-course-list-in-progress',
                             childView: CourseCardView,
                             collection: this.inProgressCourseCollection,
                             context: $.extend(this.options, {enrolled: gettext('Enrolled')})
                         }).render();
                     }

                     new SidebarView({
                         el: '.sidebar',
                         context: this.options
                     }).render();
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
