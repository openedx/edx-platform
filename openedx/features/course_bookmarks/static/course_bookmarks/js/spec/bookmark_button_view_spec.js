define([
    'backbone', 'jquery', 'underscore', 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'common/js/spec_helpers/template_helpers', 'course_bookmarks/js/views/bookmark_button'
],
function(Backbone, $, _, AjaxHelpers, TemplateHelpers, BookmarkButtonView) {
    'use strict';

    describe('BookmarkButtonView', function() {
        var createBookmarkButtonView, verifyBookmarkButtonState;

        var API_URL = 'bookmarks/api/v1/bookmarks/';

        beforeEach(function() {
            loadFixtures('course_bookmarks/fixtures/bookmark_button.html');
            TemplateHelpers.installTemplates(
                [
                    'templates/fields/message_banner'
                ]
            );

            jasmine.createSpy('timerCallback');
            jasmine.clock().install();
        });

        afterEach(function() {
            jasmine.clock().uninstall();
        });

        createBookmarkButtonView = function(isBookmarked) {
            return new BookmarkButtonView({
                el: '.bookmark-button',
                bookmarked: isBookmarked,
                bookmarkId: 'bilbo,usage_1',
                usageId: 'usage_1',
                apiUrl: API_URL
            });
        };

        verifyBookmarkButtonState = function(view, bookmarked) {
            if (bookmarked) {
                expect(view.$el).toHaveAttr('aria-pressed', 'true');
                expect(view.$el).toHaveClass('bookmarked');
            } else {
                expect(view.$el).toHaveAttr('aria-pressed', 'false');
                expect(view.$el).not.toHaveClass('bookmarked');
            }
            expect(view.$el.data('bookmarkId')).toBe('bilbo,usage_1');
        };

        it('rendered correctly', function() {
            var view = createBookmarkButtonView(false);
            verifyBookmarkButtonState(view, false);

            // with bookmarked true
            view = createBookmarkButtonView(true);
            verifyBookmarkButtonState(view, true);
        });

        it('bookmark/un-bookmark the block correctly', function() {
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

            var bookmarkedData = [[addBookmarkedData, removeBookmarkData], [removeBookmarkData, addBookmarkedData]];
            _.each(bookmarkedData, function(actionsData) {
                var firstActionData = actionsData[0];
                var secondActionData = actionsData[1];

                var bookmarkButtonView = createBookmarkButtonView(firstActionData.bookmarked);
                verifyBookmarkButtonState(bookmarkButtonView, firstActionData.bookmarked);

                spyOn(bookmarkButtonView, firstActionData.handler).and.callThrough();
                spyOnEvent(bookmarkButtonView.$el, firstActionData.event);

                bookmarkButtonView.$el.click();

                expect(bookmarkButtonView.$el).toHaveAttr('disabled', 'disabled');

                AjaxHelpers.expectRequest(
                    requests, firstActionData.method,
                    firstActionData.url,
                    firstActionData.body
                );

                expect(bookmarkButtonView[firstActionData.handler]).toHaveBeenCalled();
                AjaxHelpers.respondWithJson(requests, {});
                expect(firstActionData.event).toHaveBeenTriggeredOn(bookmarkButtonView.$el);
                bookmarkButtonView[firstActionData.handler].calls.reset();

                expect(bookmarkButtonView.$el).not.toHaveAttr('disabled');
                verifyBookmarkButtonState(bookmarkButtonView, secondActionData.bookmarked);

                spyOn(bookmarkButtonView, secondActionData.handler).and.callThrough();
                spyOnEvent(bookmarkButtonView.$el, secondActionData.event);

                bookmarkButtonView.$el.click();
                expect(bookmarkButtonView.$el).toHaveAttr('disabled', 'disabled');

                AjaxHelpers.expectRequest(
                    requests,
                    secondActionData.method,
                    secondActionData.url,
                    secondActionData.body
                );

                expect(bookmarkButtonView[secondActionData.handler]).toHaveBeenCalled();
                AjaxHelpers.respondWithJson(requests, {});
                expect(secondActionData.event).toHaveBeenTriggeredOn(bookmarkButtonView.$el);

                expect(bookmarkButtonView.$el).not.toHaveAttr('disabled');
                verifyBookmarkButtonState(bookmarkButtonView, firstActionData.bookmarked);
                bookmarkButtonView.undelegateEvents();
            });
        });

        it('shows an error message for HTTP 500', function() {
            var requests = AjaxHelpers.requests(this),
                $messageBanner = $('.message-banner'),
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

        it('removes error message after 5 seconds', function() {
            var requests = AjaxHelpers.requests(this),
                $messageBanner = $('.message-banner'),
                bookmarkButtonView = createBookmarkButtonView(false);
            bookmarkButtonView.$el.click();

            AjaxHelpers.respondWithError(requests);

            expect($messageBanner.text().trim()).toBe(bookmarkButtonView.errorMessage);

            jasmine.clock().tick(5001);
            expect($messageBanner.text().trim()).toBe('');
        });
    });
});
