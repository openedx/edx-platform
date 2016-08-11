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
             pageTpl
         ) {
             return Backbone.View.extend({
                 el: '.js-program-details-wrapper',

                 tpl: HtmlUtils.template(pageTpl),

                 initialize: function(options) {
                     this.options = options;
                     this.programModel = new Backbone.Model(this.options.programData);
                     this.courseCardCollection = new CourseCardCollection(
                        this.programModel.get('course_codes')
                    );
                     this.render();
                 },

                 render: function() {
                     HtmlUtils.setHtml(this.$el, this.tpl());
                     this.postRender();
                 },

                 postRender: function() {
                     this.headerView = new HeaderView({
                         model: new Backbone.Model(this.options)
                     });
                     new CollectionListView({
                         el: '.js-course-list',
                         childView: CourseCardView,
                         collection: this.courseCardCollection,
                         context: this.options,
                         titleContext: {
                             el: 'h2',
                             title: 'Course List'
                         }
                     }).render();
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
