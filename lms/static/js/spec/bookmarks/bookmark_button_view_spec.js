define(['backbone', 'jquery', 'underscore', 'common/js/spec_helpers/ajax_helpers',
        'common/js/spec_helpers/template_helpers', 'js/bookmarks/views/bookmark_button'
       ],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, BookmarkButtonView) {
        'use strict';

        describe("bookmarks.button", function () {

            var API_URL = 'bookmarks/api/v1/bookmarks/';

            beforeEach(function () {
                loadFixtures('js/fixtures/bookmarks/bookmark_button.html');
                TemplateHelpers.installTemplates(
                    [
                        'templates/fields/message_banner'
                    ]
                );
            });

            var createBookmarkButtonView = function(isBookmarked) {
                return new BookmarkButtonView({
                    el: '.bookmark-button',
                    bookmarked: isBookmarked,
                    bookmarkId: 'bilbo,usage_1',
                    usageId: 'usage_1',
                    apiUrl: API_URL
                });
            };

            var verifyBookmarkButtonState = function (view, bookmarked) {
                if (bookmarked) {
                    expect(view.$el).toHaveAttr('aria-pressed', 'true');
                    expect(view.$el).toHaveClass('bookmarked');
                    expect(view.$el.find('.bookmark-sr').text()).toBe('Click to remove');
                } else {
                    expect(view.$el).toHaveAttr('aria-pressed', 'false');
                    expect(view.$el).not.toHaveClass('bookmarked');
                    expect(view.$el.find('.bookmark-sr').text()).toBe('Click to add');
                }
                expect(view.$el.data('bookmarkId')).toBe('bilbo,usage_1');
            };

            it("rendered correctly ", function () {
                var view = createBookmarkButtonView(false);
                verifyBookmarkButtonState(view, false);

                // with bookmarked true
                view = createBookmarkButtonView(true);
                verifyBookmarkButtonState(view, true);
            });

            it("bookmark/un-bookmark the block correctly", function () {
                var addBookmarkedData = {
                    bookmarked: true,
                    handler: 'removeBookmark',
                    event: 'bookmark:remove',
                    method: 'DELETE',
                    url: API_URL + 'bilbo,usage_1/',
                    body: null
                };
                var removeBookmarkData = {
                    bookmarked: false,
                    handler: 'addBookmark',
                    event: 'bookmark:add',
                    method: 'POST',
                    url: API_URL,
                    body: 'usage_id=usage_1'
                };
                var requests = AjaxHelpers.requests(this);

                _.each([[addBookmarkedData, removeBookmarkData], [removeBookmarkData, addBookmarkedData]], function(actionsData) {
                    var firstActionData = actionsData[0];
                    var secondActionData =  actionsData[1];

                    var bookmarkButtonView = createBookmarkButtonView(firstActionData.bookmarked);
                    verifyBookmarkButtonState(bookmarkButtonView, firstActionData.bookmarked);

                    spyOn(bookmarkButtonView, firstActionData.handler).andCallThrough();
                    spyOnEvent(bookmarkButtonView.$el, firstActionData.event);

                    bookmarkButtonView.$el.click();

                    AjaxHelpers.expectRequest(
                        requests, firstActionData.method,
                        firstActionData.url,
                        firstActionData.body
                    );

                    expect(bookmarkButtonView[firstActionData.handler]).toHaveBeenCalled();
                    AjaxHelpers.respondWithJson(requests, {});
                    expect(firstActionData.event).toHaveBeenTriggeredOn(bookmarkButtonView.$el);
                    bookmarkButtonView[firstActionData.handler].reset();

                    verifyBookmarkButtonState(bookmarkButtonView, secondActionData.bookmarked);

                    spyOn(bookmarkButtonView, secondActionData.handler).andCallThrough();
                    spyOnEvent(bookmarkButtonView.$el, secondActionData.event);

                    bookmarkButtonView.$el.click();

                    AjaxHelpers.expectRequest(
                        requests,
                        secondActionData.method,
                        secondActionData.url,
                        secondActionData.body
                    );

                    expect(bookmarkButtonView[secondActionData.handler]).toHaveBeenCalled();
                    AjaxHelpers.respondWithJson(requests, {});
                    expect(secondActionData.event).toHaveBeenTriggeredOn(bookmarkButtonView.$el);

                    verifyBookmarkButtonState(bookmarkButtonView, firstActionData.bookmarked);
                });

            });

            it("shows an error message for HTTP 500", function () {
                var requests = AjaxHelpers.requests(this),
                    $messageBanner = $('.coursewide-message-banner'),
                    bookmarkButtonView = createBookmarkButtonView(false);
                bookmarkButtonView.$el.click();

                AjaxHelpers.respondWithError(requests);

                expect($messageBanner.text().trim()).toBe(bookmarkButtonView.errorMessage);

                // For bookmarked button.
                bookmarkButtonView = createBookmarkButtonView(true);
                bookmarkButtonView.$el.click();

                AjaxHelpers.respondWithError(requests);

                expect($messageBanner.text().trim()).toBe(bookmarkButtonView.errorMessage);
            });

        });
    });
