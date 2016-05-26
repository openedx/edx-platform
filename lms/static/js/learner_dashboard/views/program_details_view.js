;(function (define) {
    'use strict';

    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'edx-ui-toolkit/js/utils/html-utils',
            'js/learner_dashboard/views/program_header_view',
            'text!../../../templates/learner_dashboard/program_details_view.underscore'
           ],
         function(Backbone, $, _, gettext, HtmlUtils, HeaderView, pageTpl) {
            return Backbone.View.extend({
                el: '.js-program-details-wrapper',

                tpl: HtmlUtils.template(pageTpl),

                initialize: function(options) {
                    this.programModel = new Backbone.Model(options);
                    this.render();
                },

                render: function() {
                    HtmlUtils.setHtml(this.$el, this.tpl());
                    this.postRender();
                },

                postRender: function() {
                    this.headerView = new HeaderView({
                        model: this.programModel
                    });
                }
            });
        }
    );
}).call(this, define || RequireJS.define);
