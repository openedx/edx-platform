(function(define) {
    'use strict';
    define(['gettext', 'jquery', 'underscore', 'backbone', 'logger', 'moment', 'edx-ui-toolkit/js/utils/html-utils',
            'common/js/components/views/paging_header', 'common/js/components/views/paging_footer',
            'text!course_bookmarks/templates/bookmarks-list.underscore'
        ],
        function(gettext, $, _, Backbone, Logger, _moment, HtmlUtils,
                 PagingHeaderView, PagingFooterView, bookmarksListTemplate) {
            var moment = _moment || window.moment;

            return Backbone.View.extend({

                el: '.courseware-results',
                coursewareContentEl: '#course-content',
                coursewareResultsWrapperEl: '.courseware-results-wrapper',

                errorIcon: '<span class="fa fa-fw fa-exclamation-triangle message-error" aria-hidden="true"></span>',
                loadingIcon: '<span class="fa fa-fw fa-spinner fa-pulse message-in-progress" aria-hidden="true"></span>',  // eslint-disable-line max-len

                errorMessage: gettext('An error has occurred. Please try again.'),
                loadingMessage: gettext('Loading'),

                defaultPage: 1,

                events: {
                    'click .bookmarks-results-list-item': 'visitBookmark'
                },

                initialize: function(options) {
                    this.template = HtmlUtils.template(bookmarksListTemplate);
                    this.loadingMessageView = options.loadingMessageView;
                    this.errorMessageView = options.errorMessageView;
                    this.langCode = $(this.el).data('langCode');
                    this.pagingHeaderView = new PagingHeaderView({collection: this.collection});
                    this.pagingFooterView = new PagingFooterView({collection: this.collection});
                    this.listenTo(this.collection, 'page_changed', this.render);
                    _.bindAll(this, 'render', 'humanFriendlyDate');
                },

                render: function() {
                    var data = {
                        bookmarksCollection: this.collection,
                        humanFriendlyDate: this.humanFriendlyDate
                    };

                    HtmlUtils.setHtml(this.$el, this.template(data));
                    this.pagingHeaderView.setElement(this.$('.paging-header')).render();
                    this.pagingFooterView.setElement(this.$('.paging-footer')).render();
                    this.delegateEvents();
                    return this;
                },

                showBookmarks: function() {
                    var view = this;

                    this.hideErrorMessage();
                    this.showBookmarksContainer();

                    this.collection.getPage(this.defaultPage).done(function() {
                        view.render();
                        view.focusBookmarksElement();
                    }).fail(function() {
                        view.showErrorMessage();
                    });
                },

                visitBookmark: function(event) {
                    var $bookmarkedComponent = $(event.currentTarget),
                        bookmarkId = $bookmarkedComponent.data('bookmarkId'),
                        componentUsageId = $bookmarkedComponent.data('usageId'),
                        componentType = $bookmarkedComponent.data('componentType');
                    Logger.log(
                        'edx.bookmark.accessed',
                        {
                            bookmark_id: bookmarkId,
                            component_type: componentType,
                            component_usage_id: componentUsageId
                        }
                    ).always(function() {
                        window.location.href = event.currentTarget.pathname;
                    });
                },

                /**
                 * Convert ISO 8601 formatted date into human friendly format.
                 *
                 * e.g, `2014-05-23T14:00:00Z` to `May 23, 2014`
                 *
                 * @param {String} isoDate - ISO 8601 formatted date string.
                 */
                humanFriendlyDate: function(isoDate) {
                    moment.locale(this.langCode);
                    return moment(isoDate).format('LL');
                },

                showBookmarksContainer: function() {
                    $(this.coursewareContentEl).hide();
                    // Empty el if it's not empty to get the clean state.
                    this.$el.html('');
                    this.$el.show();
                },

                showLoadingMessage: function() {
                    this.loadingMessageView.showMessage(this.loadingMessage, this.loadingIcon);
                },

                hideLoadingMessage: function() {
                    this.loadingMessageView.hideMessage();
                },

                showErrorMessage: function() {
                    this.errorMessageView.showMessage(this.errorMessage, this.errorIcon);
                },

                hideErrorMessage: function() {
                    this.errorMessageView.hideMessage();
                },

                focusBookmarksElement: function() {
                    this.$('#my-bookmarks').focus();
                }
            });
        });
}).call(this, define || RequireJS.define);
