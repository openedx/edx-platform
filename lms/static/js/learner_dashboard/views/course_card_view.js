;(function (define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'edx-ui-toolkit/js/utils/html-utils',
            'js/learner_dashboard/models/course_enroll_model',
            'js/learner_dashboard/views/course_enroll_view',
            'text!../../../templates/learner_dashboard/course_card.underscore'
           ],
         function(
             Backbone,
             $,
             _,
             gettext,
             HtmlUtils,
             EnrollModel,
             CourseEnrollView,
             pageTpl
         ) {
            return Backbone.View.extend({
                className: 'course-card card',

                tpl: HtmlUtils.template(pageTpl),

                initialize: function(options) {
                    this.enrollModel = new EnrollModel();
                    if(options.context && options.context.urls){
                        this.urlModel = new Backbone.Model(options.context.urls);
                        this.enrollModel.urlRoot = this.urlModel.get('commerce_api_url'); 
                    }
                    this.render();
                    this.listenTo(this.model, 'change', this.render);
                },

                render: function() {
                    var filledTemplate = this.tpl(this.model.toJSON());
                    HtmlUtils.setHtml(this.$el, filledTemplate);
                    this.postRender();
                },

                postRender: function(){
                    this.enrollView = new CourseEnrollView({
                        $parentEl: this.$('.course-actions'),
                        model: this.model,
                        urlModel: this.urlModel,
                        enrollModel: this.enrollModel
                    });
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
