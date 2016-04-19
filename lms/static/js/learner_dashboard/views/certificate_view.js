;(function (define) {
    'use strict';
    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'text!../../../templates/learner_dashboard/certificate.underscore'
           ],
         function(
             Backbone,
             $,
             _,
             gettext,
             certificateTpl
         ) {
            return Backbone.View.extend({
                el: '.certificates-list',
                tpl: _.template(certificateTpl),
                initialize: function(data) {
                    this.context = data.context;
                    this.render();
                },
                render: function() {
                    if (this.context.certificatesData.length > 0) {
                        this.$el.html(this.tpl(this.context));
                    }
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
