;(function (define) {

define([
    'jquery',
    'underscore',
    'backbone',
    'gettext',
], function ($, _, Backbone, gettext) {
    'use strict';

    return Backbone.View.extend({

        el: '#dashboard-revisions',
        revisionListTemplateId: '#dashboard_revision_list-tpl',
        revisionListItemTemplateId: '#dashboard_revision_item-tpl',
        loadingTemplateId: '#dashboard_revision_loading-tpl',
        errorTemplateId: '#dashboard_revision_error-tpl',
        events: {},

        initialize: function () {
            this.revisionListTemplate = _.template($(this.revisionListTemplateId).html());
            this.revisionListItemTemplate = _.template($(this.revisionListItemTemplateId).html());
            this.loadingTemplate = _.template($(this.loadingTemplateId).html());
            this.errorTemplate = _.template($(this.errorTemplateId).html());
            this.showLoadingMessage();
        },

        render: function () {
            this.$el.html(this.revisionListTemplate({
                totalCount: this.collection.length,
            }));
            this.renderItems();
            return this;
        },

        renderItems: function () {
            var items = this.collection.map(function (revision) {
                var data = _.clone(revision.attributes);
                return this.revisionListItemTemplate(data);
            }, this);
            this.$el.find('ul').html(items.join(''));
        },

        showLoadingMessage: function () {
            this.$el.html(this.loadingTemplate());
        },

        showErrorMessage: function () {
            this.$el.html(this.errorTemplate());
        },

    });

});


})(define || RequireJS.define);
