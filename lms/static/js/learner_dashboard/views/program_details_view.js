;(function (define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'text!../../../templates/learner_dashboard/program_details_view.underscore'
           ],
         function(
             Backbone,
             $,
             _,
             gettext,
             pageTpl
         ) {
            return Backbone.View.extend({
                el: '.js-program-details-wrapper',

                tpl: _.template(pageTpl),

                initialize: function(data) {
                    this.context = data.context;
                    this.render();
                },

                render: function() {
                    this.$el.html(this.tpl(this.context));
                    this.postRender();
                },

                postRender: function() {
                    // Add subviews
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
