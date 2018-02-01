import gettext from 'gettext';
import $ from 'jquery';
import _ from 'underscore';
import Backbone from 'backbone';
import MessageBannerView from 'js/views/message_banner';


function BookmarkButton() {
  return Backbone.View.extend({
    errorMessage: gettext('An error has occurred. Please try again.'),

    bookmarkText: gettext('Bookmark this page'),
    bookmarkedText: gettext('Bookmarked'),

    events: {
      click: 'toggleBookmark',
    },

    showBannerInterval: 5000,   // time in ms

    initialize(options) {
      this.apiUrl = options.apiUrl;
      this.bookmarkId = options.bookmarkId;
      this.bookmarked = options.bookmarked;
      this.usageId = options.usageId;
      this.setBookmarkState(this.bookmarked);
    },

    toggleBookmark(event) {
      event.preventDefault();

      this.$el.prop('disabled', true);

      if (this.$el.hasClass('bookmarked')) {
        this.removeBookmark();
      } else {
        this.addBookmark();
      }
    },

    addBookmark() {
      const view = this;
      $.ajax({
        data: { usage_id: view.usageId },
        type: 'POST',
        url: view.apiUrl,
        dataType: 'json',
        success() {
          view.$el.trigger('bookmark:add');
          view.setBookmarkState(true);
        },
        error(jqXHR) {
          let response;
          let userMessage;
          try {
            response = jqXHR.responseText ? JSON.parse(jqXHR.responseText) : '';
            userMessage = response ? response.user_message : '';
            view.showError(userMessage);
          } catch (err) {
            view.showError();
          }
        },
        complete() {
          view.$el.prop('disabled', false);
          view.$el.focus();
        },
      });
    },

    removeBookmark() {
      const view = this;
      const deleteUrl = `${view.apiUrl + view.bookmarkId}/`;

      $.ajax({
        type: 'DELETE',
        url: deleteUrl,
        success() {
          view.$el.trigger('bookmark:remove');
          view.setBookmarkState(false);
        },
        error() {
          view.showError();
        },
        complete() {
          view.$el.prop('disabled', false);
          view.$el.focus();
        },
      });
    },

    setBookmarkState(bookmarked) {
      if (bookmarked) {
        this.$el.addClass('bookmarked');
        this.$el.attr('aria-pressed', 'true');
        this.$el.find('.bookmark-text').text(this.bookmarkedText);
      } else {
        this.$el.removeClass('bookmarked');
        this.$el.attr('aria-pressed', 'false');
        this.$el.find('.bookmark-text').text(this.bookmarkText);
      }
    },

    showError(errorText) {
      const errorMsg = errorText || this.errorMessage;

      if (!this.messageView) {
        this.messageView = new MessageBannerView({
          el: $('.message-banner'),
          type: 'error',
        });
      }
      this.messageView.showMessage(errorMsg);

                    // Hide message automatically after some interval
      setTimeout(_.bind(() => {
        this.messageView.hideMessage();
      }, this), this.showBannerInterval);
    },
  });
}
export default BookmarkButton;
