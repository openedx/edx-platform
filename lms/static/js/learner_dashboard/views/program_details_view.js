(function(define) {
    'use strict';
    define(['backbone',
        'jquery',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'js/learner_dashboard/collections/course_card_collection',
        'js/learner_dashboard/views/program_header_view',
        'js/learner_dashboard/views/collection_list_view',
        'js/learner_dashboard/views/course_card_view',
        'js/learner_dashboard/views/program_details_sidebar_view',
        'text!../../../templates/learner_dashboard/program_details_view.underscore'
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

                 events: {
                     'click .complete-program': 'trackPurchase'
                 },

                 initialize: function(options) {
                     this.options = options;

                     console.log(this.courseData);

                     this.programModel = new Backbone.Model(this.options.programData);
                     this.courseData = new Backbone.Model(this.options.courseData);
                     this.certificateCollection = new Backbone.Collection(this.options.certificateData);
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

                 getUrl: function(base, programData) {
                     if (programData.uuid) {
                         return base + '&bundle=' + encodeURIComponent(programData.uuid);
                     }
                     return base;
                 },

                 render: function() {
                     var completedCount = this.completedCourseCollection.length,
                         inProgressCount = this.inProgressCourseCollection.length,
                         remainingCount = this.remainingCourseCollection.length,
                         totalCount = completedCount + inProgressCount + remainingCount,
                         buyButtonUrl = this.getUrl(this.options.urls.buy_button_url, this.options.programData),
                         data = {
                             totalCount: totalCount,
                             inProgressCount: inProgressCount,
                             remainingCount: remainingCount,
                             completedCount: completedCount,
                             completeProgramURL: buyButtonUrl
                         };
                     data = $.extend(data, this.programModel.toJSON());
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
                             context: $.extend(this.options, {collectionCourseStatus: 'remaining'})
                         }).render();
                     }

                     if (this.completedCourseCollection.length > 0) {
                         new CollectionListView({
                             el: '.js-course-list-completed',
                             childView: CourseCardView,
                             collection: this.completedCourseCollection,
                             context: $.extend(this.options, {collectionCourseStatus: 'completed'})
                         }).render();
                     }

                     if (this.inProgressCourseCollection.length > 0) {
                         // This is last because the context is modified below
                         new CollectionListView({
                             el: '.js-course-list-in-progress',
                             childView: CourseCardView,
                             collection: this.inProgressCourseCollection,
                             context: $.extend(this.options,
                               {enrolled: gettext('Enrolled'), collectionCourseStatus: 'in_progress'}
                             )
                         }).render();
                     }

                     this.sidebarView = new SidebarView({
                         el: '.js-program-sidebar',
                         model: this.programModel,
                         courseModel: this.courseData,
                         certificateCollection: this.certificateCollection
                     });
                 },

                 trackPurchase: function() {
                     var data = this.options.programData;
                     window.analytics.track('edx.bi.user.dashboard.program.purchase', {
                         category: data.variant + ' bundle',
                         label: data.title,
                         uuid: data.uuid
                     });
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
