(function(define) {
    'use strict';
    define(['backbone',
            'jquery',
            'underscore',
            'gettext',
            'edx-ui-toolkit/js/utils/html-utils',
            'text!../../../templates/learner_dashboard/upgrade_message.underscore',
            'text!../../../templates/learner_dashboard/certificate_icon.underscore'
           ],
         function(
             Backbone,
             $,
             _,
             gettext,
             HtmlUtils,
             upgradeMessageTpl,
             certificateIconTpl
         ) {
             return Backbone.View.extend({
                 messageTpl: HtmlUtils.template(upgradeMessageTpl),
                 iconTpl: HtmlUtils.template(certificateIconTpl),

                 initialize: function(options) {
                     this.$el = options.$el;
                     this.render();
                 },

                 render: function() {
                     var data = this.model.toJSON();

                     data = $.extend(data, {certificateSvg: this.iconTpl()});
                     HtmlUtils.setHtml(this.$el, this.messageTpl(data));
                 }
             });
         }
    );
}).call(this, define || RequireJS.define);
