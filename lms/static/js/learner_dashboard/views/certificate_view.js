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
                    var certificatesData = this.context.certificatesData || [];

                    if (certificatesData.length) {
                        this.$el.html(this.tpl(this.context));
                    } else {
                        /**
                         *  If not rendering remove el because
                         *  styles are applied to it
                         */
                        this.remove();
                    }
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
