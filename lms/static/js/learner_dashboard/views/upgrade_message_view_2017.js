(function(define) {
    'use strict';
    define(['backbone',
        'jquery',
        'underscore',
        'gettext',
        'edx-ui-toolkit/js/utils/html-utils',
        'text!../../../templates/learner_dashboard/upgrade_message_2017.underscore'
    ],
         function(
             Backbone,
             $,
             _,
             gettext,
             HtmlUtils,
             upgradeMessageTpl
         ) {
             return Backbone.View.extend({
                 messageTpl: HtmlUtils.template(upgradeMessageTpl),

                 initialize: function(options) {
                     this.$el = options.$el;
                     this.render();
                 },

                 render: function() {
                     var data = this.model.toJSON();

                     HtmlUtils.setHtml(this.$el, this.messageTpl(data));
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
