/**
 * MoveXBlockBreadcrumb show breadcrumbs to move back to parent.
 */
define([
    'jquery', 'backbone', 'underscore', 'gettext',
    'edx-ui-toolkit/js/utils/html-utils',
    'edx-ui-toolkit/js/utils/string-utils',
    'text!templates/move-xblock-breadcrumb.underscore'
],
function($, Backbone, _, gettext, HtmlUtils, StringUtils, MoveXBlockBreadcrumbViewTemplate) {
    'use strict';

    var MoveXBlockBreadcrumb = Backbone.View.extend({
        el: '.breadcrumb-container',

        events: {
            'click .parent-nav-button': 'handleBreadcrumbButtonPress'
        },

        initialize: function() {
            this.template = HtmlUtils.template(MoveXBlockBreadcrumbViewTemplate);
            this.listenTo(Backbone, 'move:childrenRendered', this.render);
        },

        render: function(options) {
            HtmlUtils.setHtml(
                this.$el,
                this.template(options)
            );
            Backbone.trigger('move:breadcrumbRendered');
            return this;
        },

        /**
         * Event handler for breadcrumb button press.
         *
         * @param {Object} event
         */
        handleBreadcrumbButtonPress: function(event) {
            Backbone.trigger(
                'move:breadcrumbButtonPressed',
                $(event.target).data('parentIndex')
            );
        }
    });

    return MoveXBlockBreadcrumb;
});
