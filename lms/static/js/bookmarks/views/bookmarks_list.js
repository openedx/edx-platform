;(function (define, undefined) {
    'use strict';
    define(['gettext', 'jquery', 'underscore', 'backbone', 'logger', 'moment'],
        function (gettext, $, _, Backbone, Logger, _moment) {

        var moment = _moment || window.moment;

        return Backbone.View.extend({

            el: '.courseware-results',
            coursewareContentEl: '#course-content',

            errorIcon: '<i class="fa fa-fw fa-exclamation-triangle message-error" aria-hidden="true"></i>',
            loadingIcon: '<i class="fa fa-fw fa-spinner fa-pulse message-in-progress" aria-hidden="true"></i>',

            errorMessage: gettext('An error has occurred. Please try again.'),
            loadingMessage: gettext('Loading'),

            PAGE_SIZE: 500,

            events : {
                'click .bookmarks-results-list-item': 'visitBookmark'
            },

            initialize: function (options) {
                this.template = _.template($('#bookmarks_list-tpl').text());
                this.loadingMessageView = options.loadingMessageView;
                this.errorMessageView = options.errorMessageView;
                this.courseId = $(this.el).data('courseId');
                this.langCode = $(this.el).data('langCode');
                _.bindAll(this, 'render', 'humanFriendlyDate');
            },

            render: function () {
                var data = {
                    bookmarks: this.collection.models,
                    humanFriendlyDate: this.humanFriendlyDate
                };
                this.$el.html(this.template(data));
                this.delegateEvents();
                return this;
            },

            showBookmarks: function () {
                var view = this;

                this.hideErrorMessage();
                this.showBookmarksContainer();
                this.showLoadingMessage();

                this.collection.fetch({
                    reset: true,
                    data: {course_id: this.courseId, page_size: this.PAGE_SIZE, fields: 'display_name,path'}
                }).done(function () {
                    view.hideLoadingMessage();
                    view.render();
                    view.focusBookmarksElement();
                }).fail(function () {
                    view.hideLoadingMessage();
                    view.showErrorMessage();
                });
            },

            visitBookmark: function (event) {
                var bookmarkedComponent = $(event.currentTarget);
                var bookmark_id = bookmarkedComponent.data('bookmarkId');
                var component_usage_id = bookmarkedComponent.data('usageId');
                var component_type = bookmarkedComponent.data('componentType');
                Logger.log(
                    'edx.bookmark.accessed',
                    {
                       bookmark_id: bookmark_id,
                       component_type: component_type,
                       component_usage_id: component_usage_id
                    }
                ).always(function () {
                    window.location.href = event.currentTarget.pathname;
                });
            },

            /**
             * Convert ISO 8601 formatted date into human friendly format. e.g, `2014-05-23T14:00:00Z` to `May 23, 2014`
             * @param {String} isoDate - ISO 8601 formatted date string.
             */
            humanFriendlyDate: function (isoDate) {
                moment.locale(this.langCode);
                return moment(isoDate).format('LL');
            },

            areBookmarksVisible: function () {
                return this.$('#my-bookmarks').is(":visible");
            },

            hideBookmarks: function () {
              this.$el.hide();
              $(this.coursewareContentEl).show();
            },

            showBookmarksContainer: function () {
                $(this.coursewareContentEl).hide();
                // Empty el if it's not empty to get the clean state.
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
