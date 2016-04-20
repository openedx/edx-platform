;(function (define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'js/learner_dashboard/views/explore_new_programs_view',
            'text!../../../templates/learner_dashboard/sidebar.underscore'
           ],
         function(
             Backbone,
             $,
             _,
             gettext,
             NewProgramsView,
             sidebarTpl
         ) {
            return Backbone.View.extend({
                el: '.sidebar',

                tpl: _.template(sidebarTpl),

                initialize: function(data) {
                    this.context = data.context;
                },

                render: function() {
                    this.$el.html(this.tpl(this.context));
                    this.postRender();
                },

                postRender: function() {
                    this.newProgramsView = new NewProgramsView({
                        context: this.context
                    });
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
