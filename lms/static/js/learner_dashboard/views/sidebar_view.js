;(function (define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'text!../../../templates/learner_dashboard/sidebar.underscore'
           ],
         function(
             Backbone,
             $,
             _,
             gettext,
             sidebarTpl
         ) {
            return Backbone.View.extend({
                el: '.sidebar',
                tpl: _.template(sidebarTpl),
                initialize: function(data) {
                    this.context = data.context;
                },
                render: function() {
                    if (this.context.xseriesUrl){
                        //Only show the xseries advertising panel if the link is passed in
                        this.$el.html(this.tpl(this.context));
                    }
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
