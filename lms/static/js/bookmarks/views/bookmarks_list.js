;(function (define, undefined) {
    'use strict';
    define(['gettext', 'jquery', 'underscore', 'backbone', 'logger', 'moment',
            'common/js/components/views/paging_header', 'common/js/components/views/paging_footer',
            'text!templates/bookmarks/bookmarks-list.underscore'
        ],
        function (gettext, $, _, Backbone, Logger, _moment,
                  PagingHeaderView, PagingFooterView, BookmarksListTemplate) {

        var moment = _moment || window.moment;

        return Backbone.View.extend({

            el: '.courseware-results',
            coursewareContentEl: '#course-content',
            coursewareResultsWrapperEl: '.courseware-results-wrapper',

            errorIcon: '<i class="fa fa-fw fa-exclamation-triangle message-error" aria-hidden="true"></i>',
            loadingIcon: '<i class="fa fa-fw fa-spinner fa-pulse message-in-progress" aria-hidden="true"></i>',

            errorMessage: gettext('An error has occurred. Please try again.'),
            loadingMessage: gettext('Loading'),

            defaultPage: 1,

            events : {
                'click .bookmarks-results-list-item': 'visitBookmark'
            },

            initialize: function (options) {
                this.template = _.template(BookmarksListTemplate);
                this.loadingMessageView = options.loadingMessageView;
                this.errorMessageView = options.errorMessageView;
                this.langCode = $(this.el).data('langCode');
                this.pagingHeaderView = new PagingHeaderView({collection: this.collection});
                this.pagingFooterView = new PagingFooterView({collection: this.collection});
                this.listenTo(this.collection, 'page_changed', this.render);
                _.bindAll(this, 'render', 'humanFriendlyDate');
            },

            render: function () {
                var data = {
                    bookmarksCollection: this.collection,
                    humanFriendlyDate: this.humanFriendlyDate
                };
                this.$el.html(this.template(data));
                this.pagingHeaderView.setElement(this.$('.paging-header')).render();
                this.pagingFooterView.setElement(this.$('.paging-footer')).render();
                this.delegateEvents();
                return this;
            },

            showBookmarks: function () {
                var view = this;

                this.hideErrorMessage();
                this.showBookmarksContainer();

                this.collection.goTo(this.defaultPage).done(function () {
                    view.render();
                    view.focusBookmarksElement();
                }).fail(function () {
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
                $(this.coursewareResultsWrapperEl).hide();
                $(this.coursewareContentEl).css( 'display', 'table-cell');
            },

            showBookmarksContainer: function () {
                $(this.coursewareContentEl).hide();
                // Empty el if it's not empty to get the clean state.
                this.$el.html('');
                this.$el.show();
                $(this.coursewareResultsWrapperEl).css('display', 'table-cell');
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
