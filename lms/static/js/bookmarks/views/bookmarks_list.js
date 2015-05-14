;(function (define, undefined) {
    'use strict';
    define(['gettext', 'jquery', 'underscore', 'backbone', 'js/views/message'],
        function (gettext, $, _, Backbone, MessageView) {

        return Backbone.View.extend({

            el: '#courseware-results-list',
            coursewareContentElement: '#course-content',

            errorIcon: '<i class="fa fa-fw fa-exclamation-triangle message-error" aria-hidden="true"></i>',
            loadingIcon: '<i class="fa fa-fw fa-spinner fa-pulse message-in-progress" aria-hidden="true"></i>',

            errorMessage: gettext('An error has occurred. Please try again.'),
            loadingMessage: gettext('Loading'),

            url: '/api/bookmarks/v1/bookmarksss',

            initialize: function (options) {
                this.template = _.template($('#bookmarks_list-tpl').text());
                this.loadingMessageView = options.loadingMessageView;
                this.errorMessageView = options.errorMessageView;
                _.bindAll(this, 'render');
            },

            render: function () {
                var data = {
                    bookmarks: this.collection.models,
                    breadcrumbTrail: this.breadcrumbTrail,
                    userFriendlyDate: this.userFriendlyDate
                };
                this.$el.html(this.template(data));
                return this;
            },

            loadBookmarks: function () {
                var view = this;

                this.hideErrorMessage();
                this.showBookmarksContainer();
                this.showLoadingMessage();

                this.collection.url = this.url;
                this.collection.fetch({
                    reset: true,
                    data: {course_id: 'a/b/c', fields: 'path', page: 1, page_size: 65536}
                }).done(function () {
                    view.hideLoadingMessage();
                    view.render();
                    view.focusBookmarksElement();
                }).fail(function () {
                    view.hideLoadingMessage();
                    view.showErrorMessage();
                });
            },

            breadcrumbTrail: function (bookmarkPath) {
                var separator = ' <i class="icon fa fa-caret-right" aria-hidden="true"></i><span class="sr">-</span> ';
                return _.pluck(bookmarkPath, 'display_name').join(separator);
            },

            // TODO! This utility method will be moved to some proper place OR maybe remove at all.
            userFriendlyDate: function (isoDate) {
                // Convert ISO 8601 date string to user friendly format
                // "2014-09-23T14:00:00Z"     >>      September 23, 2014
                var dt = new Date(isoDate);
                var MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
                return MONTHS[dt.getMonth()] + ' ' + dt.getDay() + ', ' + dt.getFullYear();
            },

            isVisible: function () {
                return this.$('#my-bookmarks').is(":visible");
            },

            hideBookmarks: function () {
              this.$el.hide();
              $(this.coursewareContentElement).show();
            },

            showBookmarksContainer: function () {
                $(this.coursewareContentElement).hide();
                // Empty it if there anything in it.
                this.$el.html('');
                this.$el.show();
            },

            showLoadingMessage: function () {
                this.loadingMessageView.showMessage(this.loadingMessage, this.loadingIcon);
            },

            hideLoadingMessage: function () {
                this.loadingMessageView.hideMessage();
            },

            showErrorMessage: function () {
                this.errorMessageView.showMessage(this.errorMessage, this.errorIcon);
            },

            hideErrorMessage: function () {
                this.errorMessageView.hideMessage();
            },

            focusBookmarksElement: function () {
                this.$('#my-bookmarks').focus();
            }
        });
    });
}).call(this, define || RequireJS.define);
