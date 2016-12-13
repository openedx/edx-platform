/**
 * A generic header view class.
 */
(function(define) {
    'use strict';
    define(['backbone',
            'edx-ui-toolkit/js/utils/html-utils',
            'text!templates/components/header/header.underscore'],
           function(Backbone, HtmlUtils, headerTemplate) {
               var HeaderView = Backbone.View.extend({
                   initialize: function(options) {
                       this.template = HtmlUtils.template(headerTemplate);
                       this.headerActionsView = options.headerActionsView;
                       this.listenTo(this.model, 'change', this.render);
                       this.render();
                   },

                   render: function() {
                       var json = this.model.attributes;
                       HtmlUtils.setHtml(
                           this.$el,
                           this.template(json)
                       );
                       if (this.headerActionsView) {
                           this.headerActionsView.setElement(this.$('.page-header-secondary')).render();
                       }
                       return this;
                   }
               });

               return HeaderView;
           });
}).call(this, define || RequireJS.define);
