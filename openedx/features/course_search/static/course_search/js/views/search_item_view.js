(function(define) {
    'use strict';

    define([
        'jquery',
        'underscore',
        'backbone',
        'gettext',
        'logger',
        'edx-ui-toolkit/js/utils/html-utils'
    ], function($, _, Backbone, gettext, Logger, HtmlUtils) {
        return Backbone.View.extend({

            tagName: 'li',
            className: 'search-results-item',
            attributes: {
                role: 'region',
                'aria-label': 'search result'
            },

            events: {
                click: 'logSearchItem'
            },

            initialize: function(options) {
                this.template = options.template;
            },

            unitIcon: function() {
                var icon = null;
                switch (this.model.attributes.content_type) {
                case 'Video':
                    icon = 'film';
                    break;
                case 'CAPA':
                    icon = 'edit';
                    break;
                case 'Sequence':
                    icon = 'compass';
                    break;
                default:
                    icon = 'book';
                    break;
                }
                return icon;
            },

            render: function() {
                var data = _.clone(this.model.attributes);

                // Drop the preview text and result type if the search term is found
                // in the title/location in the course hierarchy
                if (this.model.get('content_type') === 'Sequence') {
                    data.excerpt = '';
                    data.content_type = '';
                }
                data.unit_icon = this.unitIcon();
                data.excerptHtml = HtmlUtils.HTML(data.excerpt);
                delete data.excerpt;
                HtmlUtils.setHtml(this.$el, HtmlUtils.template(this.template)(data));
                return this;
            },

            /**
         * Redirect to a URL.  Mainly useful for mocking out in tests.
         * @param  {string} url The URL to redirect to.
         */
            redirect: function(url) {
                window.location.href = url;
            },

            logSearchItem: function(event) {
                var self = this;
                var target = this.model.id;
                var link = this.model.get('url');
                var collection = this.model.collection;
                var page = collection.page;
                var pageSize = collection.pageSize;
                var searchTerm = collection.searchTerm;
                var index = collection.indexOf(this.model);

                event.preventDefault();

                Logger.log('edx.course.search.result_selected', {
                    search_term: searchTerm,
                    result_position: (page * pageSize) + index,
                    result_link: target
                }).always(function() {
                    self.redirect(link);
                });
            }

        });
    });
}(define || RequireJS.define));
