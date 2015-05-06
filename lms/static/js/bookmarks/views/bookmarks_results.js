;(function (define, undefined) {
    'use strict';
    define(['gettext', 'jquery', 'underscore', 'backbone'],
        function (gettext, $, _, Backbone) {

        var BookmarksResultsView = Backbone.View.extend({

            el: '#courseware-search-results',
            contentElement: '#course-content',

            'error': '<i class="fa fa-exclamation-triangle message-error" aria-hidden="true"></i><span class="sr">' + gettext("Error") + '</span>',
            'loading': '<i class="fa fa-spinner fa-pulse message-in-progress" aria-hidden="true"></i><span class="sr">' + gettext("Loading") + '</span>',

            'errorMessage': gettext('An error has occurred. Please try again.'),
            'loadingMessage': gettext('Loading'),

            events: {
            },

            initialize: function () {
                this.template = _.template($('#bookmarks_results-tpl').text());
                _.bindAll(this, 'render');
            },

            render: function () {
                this.$el.html(this.template({
                    bookmarks: this.collection.models
                }));
                return this;
            },

            bookmarksShown: function () {
                return this.$("#my-bookmarks").is(":visible");
            },

            hideBookmarks: function () {
              this.$el.hide();
              $(this.contentElement).show();
            },

            url: function () {
                return '/api/bookmarks/v1/bookmarks';
            },

            loadBookmarks: function () {
                var view = this;

                this.toggleElementsVisibility();
                this.showLoadingMessage();

                this.collection.url = this.url();
                this.collection.fetch({
                    reset: true,
                    data: {course_id: '', fields: 'path'}
                }).done(function () {
                    view.render();
                    view.setFocusAfterBookmarksLoaded();
                }).fail(function () {
                    view.showErrorMessage();
                });
            },

            toggleElementsVisibility: function () {
                $(this.contentElement).hide();
                this.$el.show();
            },

            showLoadingMessage: function () {
                $(this.el).html(this.loading + ' ' + this.loadingMessage);
            },

            showErrorMessage: function () {
                $(this.el).html(this.error + ' ' + this.errorMessage);
            },

            setFocusAfterBookmarksLoaded: function () {
                this.$('#my-bookmarks').focus();
            }
        });

        return BookmarksResultsView;
    });
}).call(this, define || RequireJS.define);
