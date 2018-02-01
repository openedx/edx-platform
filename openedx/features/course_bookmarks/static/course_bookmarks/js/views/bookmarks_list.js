import gettext from 'gettext';
import $ from 'jquery';
import _ from 'underscore';
import Backbone from 'backbone';
import Logger from 'logger';
import _moment from 'moment';
import HtmlUtils from 'edx-ui-toolkit/js/utils/html-utils';
import PagingHeaderView from 'common/js/components/views/paging_header';
import PagingFooterView from 'common/js/components/views/paging_footer';
import bookmarksListTemplate from 'course_bookmarks/templates/bookmarks-list.underscore';

function BookmarksList() {
  const moment = _moment || window.moment;

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
      'click .bookmarks-results-list-item': 'visitBookmark',
    },

    initialize(options) {
      this.template = HtmlUtils.template(bookmarksListTemplate);
      this.loadingMessageView = options.loadingMessageView;
      this.errorMessageView = options.errorMessageView;
      this.langCode = $(this.el).data('langCode');
      this.pagingHeaderView = new PagingHeaderView({ collection: this.collection });
      this.pagingFooterView = new PagingFooterView({ collection: this.collection });
      this.listenTo(this.collection, 'page_changed', this.render);
      _.bindAll(this, 'render', 'humanFriendlyDate');
    },

    render() {
      const data = {
        bookmarksCollection: this.collection,
        humanFriendlyDate: this.humanFriendlyDate,
      };

      HtmlUtils.setHtml(this.$el, this.template(data));
      this.pagingHeaderView.setElement(this.$('.paging-header')).render();
      this.pagingFooterView.setElement(this.$('.paging-footer')).render();
      this.delegateEvents();
      return this;
    },

    showBookmarks() {
      const view = this;

      this.hideErrorMessage();
      this.showBookmarksContainer();

      this.collection.getPage(this.defaultPage).done(() => {
        view.render();
        view.focusBookmarksElement();
      }).fail(() => {
        view.showErrorMessage();
      });
    },

    visitBookmark(event) {
      const $bookmarkedComponent = $(event.currentTarget);
      const bookmarkId = $bookmarkedComponent.data('bookmarkId');
      const componentUsageId = $bookmarkedComponent.data('usageId');
      const componentType = $bookmarkedComponent.data('componentType');
      Logger.log(
                        'edx.bookmark.accessed',
        {
          bookmark_id: bookmarkId,
          component_type: componentType,
          component_usage_id: componentUsageId,
        },
                    ).always(() => {
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
    humanFriendlyDate(isoDate) {
      moment.locale(this.langCode);
      return moment(isoDate).format('LL');
    },

    showBookmarksContainer() {
      $(this.coursewareContentEl).hide();
                    // Empty el if it's not empty to get the clean state.
      this.$el.html('');
      this.$el.show();
    },

    showLoadingMessage() {
      this.loadingMessageView.showMessage(this.loadingMessage, this.loadingIcon);
    },

    hideLoadingMessage() {
      this.loadingMessageView.hideMessage();
    },

    showErrorMessage() {
      this.errorMessageView.showMessage(this.errorMessage, this.errorIcon);
    },

    hideErrorMessage() {
      this.errorMessageView.hideMessage();
    },

    focusBookmarksElement() {
      this.$('#my-bookmarks').focus();
    },
  });
}

export default BookmarksList;
