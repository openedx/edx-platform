;(function (define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'edx-ui-toolkit/js/utils/html-utils',
            'js/learner_dashboard/views/course_enroll_view',
            'text!../../../templates/learner_dashboard/course_card.underscore'
           ],
         function(
             Backbone,
             $,
             _,
             gettext,
             HtmlUtils,
             CourseEnrollView,
             pageTpl
         ) {
            return Backbone.View.extend({
                className: 'course-card card',

                tpl: HtmlUtils.template(pageTpl),

                initialize: function() {
                    this.render();
                },

                render: function() {
                    var filledTemplate = this.tpl(this.model.toJSON());
                    HtmlUtils.setHtml(this.$el, filledTemplate);
                    this.postRender();
                },

                postRender: function(){
                    this.enrollView = new CourseEnrollView({
                        $el: this.$('.course-actions'),
                        model: this.model,
                        context: this.context
                    });
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
