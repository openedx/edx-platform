/**
 * A generic header view class.
 */
(function(define) {
    'use strict';

    define([
        'backbone',
        'text!templates/components/header/header.underscore',
        'edx-ui-toolkit/js/utils/html-utils'
    ],
    function(Backbone, headerTemplate, HtmlUtils) {
        // eslint-disable-next-line no-var
        var HeaderView = Backbone.View.extend({
            initialize: function(options) {
                this.template = HtmlUtils.template(headerTemplate);
                this.headerActionsView = options.headerActionsView;
                this.listenTo(this.model, 'change', this.render);
                this.render();
            },

            render: function() {
                // eslint-disable-next-line no-var
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
// eslint-disable-next-line no-undef
}).call(this, define || RequireJS.define);
