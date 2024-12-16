(function(define) {
    'use strict';

    define(['gettext', 'jquery', 'underscore', 'backbone', 'js/views/message_banner'],
        function(gettext, $, _, Backbone, MessageBannerView) {
            return Backbone.View.extend({
                errorMessage: gettext('An error has occurred. Please try again.'),

                bookmarkText: gettext('Bookmark this page'),
                bookmarkedText: gettext('Bookmarked'),

                events: {
                    click: 'toggleBookmark'
                },

                showBannerInterval: 5000, // time in ms

                initialize: function(options) {
                    this.apiUrl = options.apiUrl;
                    this.bookmarkId = options.bookmarkId;
                    this.bookmarked = options.bookmarked;
                    this.usageId = options.usageId;
                    if (options.bookmarkedText) {
                        this.bookmarkedText = options.bookmarkedText;
                    }
                    if (options.bookmarkText) {
                        this.bookmarkText = options.bookmarkText;
                    }
                    this.setBookmarkState(this.bookmarked);
                },

                toggleBookmark: function(event) {
                    event.preventDefault();

                    this.$el.prop('disabled', true);

                    if (this.$el.hasClass('bookmarked')) {
                        this.removeBookmark();
                    } else {
                        this.addBookmark();
                    }
                },

                addBookmark: function() {
                    var view = this;
                    $.ajax({
                        data: {usage_id: view.usageId},
                        type: 'POST',
                        url: view.apiUrl,
                        dataType: 'json',
                        success: function() {
                            view.$el.trigger('bookmark:add');
                            view.setBookmarkState(true);
                        },
                        error: function(jqXHR) {
                            var response, userMessage;
                            try {
                                response = jqXHR.responseText ? JSON.parse(jqXHR.responseText) : '';
                                userMessage = response ? response.user_message : '';
                                view.showError(userMessage);
                            } catch (err) {
                                view.showError();
                            }
                        },
                        complete: function() {
                            view.$el.prop('disabled', false);
                            view.$el.focus();
                        }
                    });
                },

                removeBookmark: function() {
                    var view = this;
                    var deleteUrl = view.apiUrl + view.bookmarkId + '/';

                    $.ajax({
                        type: 'DELETE',
                        url: deleteUrl,
                        success: function() {
                            view.$el.trigger('bookmark:remove');
                            view.setBookmarkState(false);
                        },
                        error: function() {
                            view.showError();
                        },
                        complete: function() {
                            view.$el.prop('disabled', false);
                            view.$el.focus();
                        }
                    });
                },

                setBookmarkState: function(bookmarked) {
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

                showError: function(errorText) {
                    var errorMsg = errorText || this.errorMessage;

                    if (!this.messageView) {
                        this.messageView = new MessageBannerView({
                            el: $('.message-banner'),
                            type: 'error'
                        });
                    }
                    this.messageView.showMessage(errorMsg);

                    // Hide message automatically after some interval
                    setTimeout(_.bind(function() {
                        this.messageView.hideMessage();
                    }, this), this.showBannerInterval);
                }
            });
        });
}).call(this, define || RequireJS.define);
