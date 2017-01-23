/**
 * MoveXBlockBreadcrumb shows back button and breadcrumb to move back to parent.
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
        defaultRenderOptions: {
            backButtonEnabled: false,
            breadcrumbs: ['Course Outline'],
            backButtonSRText: gettext('Press button to go back to parent')
        },

        events: {
            'click .button-backward': 'handleBackButtonPress',
            'click .parent-nav-button': 'handleBreadcrumbButtonPress'
        },

        initialize: function() {
            this.template = HtmlUtils.template(MoveXBlockBreadcrumbViewTemplate);
            this.listenTo(Backbone, 'move:childsInfoRendered', this.updateView);
        },

        render: function(options) {
            HtmlUtils.setHtml(
                this.$el,
                this.template(_.extend({}, this.defaultRenderOptions, options))
            );
            return this;
        },

        handleBackButtonPress: function() {
            Backbone.trigger('move:backButtonPressed');
        },

        handleBreadcrumbButtonPress: function(event) {
            Backbone.trigger(
                'move:breadcrumbButtonPressed',
                $(event.target).data('parentIndex')
            );
        },

        updateView: function(args) {
            this.render(args);
        }
    });

    return MoveXBlockBreadcrumb;
});
