;(function (define, undefined) {
    'use strict';
    define(['gettext', 'jquery', 'underscore', 'backbone', 'js/views/message'],
        function (gettext, $, _, Backbone, MessageView) {

        return Backbone.View.extend({

            errorIcon: '<i class="fa fa-fw fa-exclamation-triangle message-error" aria-hidden="true"></i>',
            errorMessage: gettext('An error has occurred. Please try again.'),

            srAddBookmarkText: gettext('Click to add'),
            srRemoveBookmarkText: gettext('Click to remove'),

            events: {
                'click': 'toggleBookmark'
            },

            initialize: function (options) {
                this.apiUrl = options.apiUrl;
                this.bookmarkId = options.bookmarkId;
                this.bookmarked = options.bookmarked;
                this.usageId = options.usageId;
                this.setBookmarkState(this.bookmarked);
            },

            toggleBookmark: function(event) {
                event.preventDefault();

                if (this.$el.hasClass('bookmarked')) {
                    this.removeBookmark();
                } else {
                    this.addBookmark();
                }
            },

            addBookmark: function() {
                var view = this;
                $.ajax({
                    data: {usage_id:  view.usageId},
                    type: "POST",
                    url: view.apiUrl,
                    dataType: 'json',
                    success: function () {
                        view.$el.trigger('bookmark:add');
                        view.setBookmarkState(true);
                    },
                    error: function() {
                        view.showError();
                    }
                });
            },

            removeBookmark: function() {
                var view = this;
                var deleteUrl = view.apiUrl + view.bookmarkId + '/';

                $.ajax({
                    type: "DELETE",
                    url: deleteUrl,
                    success: function () {
                        view.$el.trigger('bookmark:remove');
                        view.setBookmarkState(false);
                    },
                    error: function() {
                        view.showError();
                    }
                });
            },

            setBookmarkState: function(bookmarked) {
                if (bookmarked) {
                    this.$el.addClass('bookmarked');
                    this.$el.attr('aria-pressed', 'true');
                    this.$el.find('.bookmark-sr').text(this.srRemoveBookmarkText);
                } else {
                    this.$el.removeClass('bookmarked');
                    this.$el.attr('aria-pressed', 'false');
                    this.$el.find('.bookmark-sr').text(this.srAddBookmarkText);
                }
            },

            showError: function() {
                if (!this.messageView) {
                    this.messageView = new MessageView({
                        el: $('.coursewide-message-banner'),
                        templateId: '#message_banner-tpl'
                    });
                }
                this.messageView.showMessage(this.errorMessage, this.errorIcon);
            }
        });
    });
}).call(this, define || RequireJS.define);
