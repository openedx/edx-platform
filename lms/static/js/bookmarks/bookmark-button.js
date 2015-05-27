;(function (define, undefined) {
    'use strict';
    define(['gettext', 'jquery', 'underscore', 'backbone'],
        function (gettext, $, _, Backbone) {

        return Backbone.View.extend({

            el: '#seq_content',

            events: {
                'click .bookmark-button': 'bookmark'
            },

            initialize: function () {

            },

            bookmark: function(event) {
                var $buttonElement = $(event.currentTarget);
                var usageId = $buttonElement.data("id");

                //$buttonElement.attr("disabled", true).addClass('is-disabled');

                if ($buttonElement.hasClass('bookmarked')) {
                    this.removeBookmark($buttonElement, usageId);
                } else {
                    this.addBookmark($buttonElement, usageId);
                }
            },

            addBookmark: function($this, usageId) {

                var postUrl = $this.data('url');
                $.ajax({
                    data: {usage_id: usageId},
                    type: "POST",
                    url: postUrl,
                    dataType: 'json',
                    success: function () {
                        $('.seq-book.active').find('.bookmark-icon').removeClass('is-hidden').addClass('bookmarked');
                        $this.removeClass('un-bookmarked').addClass('bookmarked');
                        //$this.attr("disabled", false);
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        //$this.attr("disabled", false);
                        ////$(".generate_certs").attr("disabled", false).removeClass('is-disabled').attr('aria-disabled', false);
                    }
                });
            },

            removeBookmark: function($this, usageId) {
                var deleteUrl = $this.data('url') + $this.data('username') + ',' + usageId;
                $.ajax({
                    type: "DELETE",
                    url: deleteUrl,
                    success: function () {
                        $('.seq-book.active').find('.bookmark-icon').removeClass('bookmarked').addClass('is-hidden');
                        $this.removeClass('bookmarked').addClass('un-bookmarked');
                        //$this.attr("disabled", false);
                    },
                    error: function(jqXHR, textStatus, errorThrown) {
                        //$this.attr("disabled", false);
                    }
                });

            }

        });
    });
}).call(this, define || RequireJS.define);

