;(function (define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'text!../../../templates/learner_dashboard/explore_new_programs.underscore'
           ],
         function(
             Backbone,
             $,
             _,
             gettext,
             exploreTpl
         ) {
            return Backbone.View.extend({
                el: '.program-advertise',

                tpl: _.template(exploreTpl),

                initialize: function(data) {
                    this.context = data.context;
                    this.$parentEl = $(this.parentEl);

                    if (this.context.marketingUrl){
                        // Only render if there is a link
                        this.render();
                    } else {
                        /**
                         *  If not rendering remove el because
                         *  styles are applied to it
                         */
                        this.remove();
                    }
                },

                render: function() {
                    this.$el.html(this.tpl(this.context));  
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
