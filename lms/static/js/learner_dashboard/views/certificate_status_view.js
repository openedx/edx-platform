;(function (define) {
    'use strict';
    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'edx-ui-toolkit/js/utils/html-utils',
            'text!../../../templates/learner_dashboard/certificate_status.underscore',
            'text!../../../templates/learner_dashboard/certificate_icon.underscore'
           ],
         function(
             Backbone,
             $,
             _,
             gettext,
             HtmlUtils,
             certificateStatusTpl,
             certificateIconTpl
         ) {
            return Backbone.View.extend({
                statusTpl: HtmlUtils.template(certificateStatusTpl),
                iconTpl: HtmlUtils.template(certificateIconTpl),

                initialize: function(options) {
                    this.$el = options.$el;
                    this.render();
                },

                render: function() {
                    var data = this.model.toJSON(),
                        $icons;

                    HtmlUtils.setHtml(this.$el, this.statusTpl(data));

                    $icons = this.$('.certificate-icon');
                    HtmlUtils.setHtml($icons, this.iconTpl());
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
