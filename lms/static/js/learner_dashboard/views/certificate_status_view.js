;(function (define) {
    'use strict';
    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'edx-ui-toolkit/js/utils/html-utils',
            'text!../../../templates/learner_dashboard/certificate_status.underscore'
           ],
         function(
             Backbone,
             $,
             _,
             gettext,
             HtmlUtils,
             certificateStatusTpl
         ) {
            return Backbone.View.extend({
                tpl: HtmlUtils.template(certificateStatusTpl),

                initialize: function(options) {
                    this.$el = options.$el;
                    this.render();
                },

                render: function() {
                    var data = this.model.toJSON();
                    HtmlUtils.setHtml(this.$el, this.tpl(data));
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
