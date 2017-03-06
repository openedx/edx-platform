;(function(define) {
    'use strict';

    define([
        'backbone',
        'underscore',
        'gettext',
        'text!../../../templates/api_admin/catalog-results.underscore',
        'text!../../../templates/api_admin/catalog-error.underscore'
    ], function (Backbone, _, gettext, catalogResultsTpl, catalogErrorTpl) {
        return Backbone.View.extend({

            events: {
                'click .preview-query': 'previewQuery'
            },

            initialize: function (options) {
                this.previewUrl = options.previewUrl;
                this.catalogApiUrl = options.catalogApiUrl;
            },

            render: function () {
                this.$('#id_query').after(
                    '<button class="preview-query">'+ gettext('Preview this query') + '</button>'
                );
                return this;
            },

            /*
             * Return the user's query, URL-encoded.
             */
            getQuery: function () {
                return encodeURIComponent(this.$("#id_query").val());
            },

            /*
             * Make a request to get the list of courses associated
             * with the user's query. On success, displays the
             * results, and on failure, displays an error message.
             */
            previewQuery: function (event) {
                event.preventDefault();
                $.ajax(this.previewUrl + '?q=' + this.getQuery(), {
                    method: 'GET',
                    success: _.bind(this.renderCourses, this),
                    error: _.bind(function () {
                        this.$('.preview-results').html(_.template(catalogErrorTpl)({}));
                    }, this)
                });
            },

            /*
             * Render a list of courses with data returned by the
             * courses API.
             */
            renderCourses: function (data) {
                this.$('.preview-results').html(_.template(catalogResultsTpl)({
                    'courses': data.results,
                    'catalogApiUrl': this.catalogApiUrl,
                }));
            },
        });
    });
}).call(this, define || RequireJS.define);
