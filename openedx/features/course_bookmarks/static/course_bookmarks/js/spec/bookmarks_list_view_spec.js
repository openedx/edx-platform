define([
    'backbone',
    'jquery',
    'underscore',
    'logger',
    'URI',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'common/js/spec_helpers/template_helpers',
    'js/views/message_banner',
    'course_bookmarks/js/spec_helpers/bookmark_helpers',
    'course_bookmarks/js/views/bookmarks_list',
    'course_bookmarks/js/collections/bookmarks'
],
    function(Backbone, $, _, Logger, URI, AjaxHelpers, TemplateHelpers, MessageBannerView,
             BookmarkHelpers, BookmarksListView, BookmarksCollection) {
        'use strict';

        describe('BookmarksListView', function() {
            var createBookmarksView, verifyRequestParams;

            beforeEach(function() {
                loadFixtures('course_bookmarks/fixtures/bookmarks.html');
                TemplateHelpers.installTemplates([
                    'templates/fields/message_banner'
                ]);
                spyOn(Logger, 'log').and.returnValue($.Deferred().resolve());
                jasmine.addMatchers({
                    toHaveBeenCalledWithUrl: function() {
                        return {
                            compare: function(actual, expectedUrl) {
                                return {
                                    pass: expectedUrl === actual.calls.mostRecent().args[0].currentTarget.pathname
                                };
                            }
                        };
                    }
                });
            });

            createBookmarksView = function() {
                var bookmarksCollection = new BookmarksCollection(
                    [],
                    {
                        course_id: BookmarkHelpers.TEST_COURSE_ID,
                        url: BookmarkHelpers.TEST_API_URL
                    }
                );
                var bookmarksView = new BookmarksListView({
                    $el: $('.course-bookmarks'),
                    collection: bookmarksCollection,
                    loadingMessageView: new MessageBannerView({el: $('#loading-message')}),
                    errorMessageView: new MessageBannerView({el: $('#error-message')})
                });
                return bookmarksView;
            };

            verifyRequestParams = function(requests, params) {
                var urlParams = (new URI(requests[requests.length - 1].url)).query(true);
                _.each(params, function(value, key) {
                    expect(urlParams[key]).toBe(value);
                });
            };

            it('can correctly render an empty bookmarks list', function() {
                var requests = AjaxHelpers.requests(this);
                var bookmarksView = createBookmarksView();
                var expectedData = BookmarkHelpers.createBookmarksData({numBookmarksToCreate: 0});

                bookmarksView.showBookmarks();
                AjaxHelpers.respondWithJson(requests, expectedData);

                expect(bookmarksView.$('.bookmarks-empty-header').text().trim()).toBe(
                    'You have not bookmarked any courseware pages yet'
                );

                expect(bookmarksView.$('.bookmarks-empty-detail-title').text().trim()).toBe(
                    'Use bookmarks to help you easily return to courseware pages. ' +
                    'To bookmark a page, click "Bookmark this page" under the page title.'
                );

                expect(bookmarksView.$('.paging-header').length).toBe(0);
                expect(bookmarksView.$('.paging-footer').length).toBe(0);
            });

            it('has rendered bookmarked list correctly', function() {
                var requests = AjaxHelpers.requests(this);
                var bookmarksView = createBookmarksView();
                var expectedData = BookmarkHelpers.createBookmarksData({numBookmarksToCreate: 3});

                bookmarksView.showBookmarks();
                verifyRequestParams(
                    requests,
                    {
                        course_id: BookmarkHelpers.TEST_COURSE_ID,
                        fields: 'display_name,path',
                        page: '1',
                        page_size: '10'
                    }
                );
                AjaxHelpers.respondWithJson(requests, expectedData);

                BookmarkHelpers.verifyBookmarkedData(bookmarksView, expectedData);

                expect(bookmarksView.$('.paging-header').length).toBe(1);
                expect(bookmarksView.$('.paging-footer').length).toBe(1);
            });

            it('calls bookmarks list render on page_changed event', function() {
                var renderSpy = spyOn(BookmarksListView.prototype, 'render');
                var listView = new BookmarksListView({
                    collection: new BookmarksCollection([], {
                        course_id: 'abc',
                        url: '/test-bookmarks/url/'
                    })
                });
                listView.collection.trigger('page_changed');
                expect(renderSpy).toHaveBeenCalled();
            });

            it('can go to a page number', function() {
                var requests = AjaxHelpers.requests(this);
                var expectedData = BookmarkHelpers.createBookmarksData(
                    {
                        numBookmarksToCreate: 10,
                        count: 12,
                        num_pages: 2,
                        current_page: 1,
                        start: 0
                    }
                );
                var bookmarksView = createBookmarksView();
                bookmarksView.showBookmarks();
                AjaxHelpers.respondWithJson(requests, expectedData);
                BookmarkHelpers.verifyBookmarkedData(bookmarksView, expectedData);

                bookmarksView.$('input#page-number-input').val('2');
                bookmarksView.$('input#page-number-input').trigger('change');

                expectedData = BookmarkHelpers.createBookmarksData(
                    {
                        numBookmarksToCreate: 2,
                        count: 12,
                        num_pages: 2,
                        current_page: 2,
                        start: 10
                    }
                );
                AjaxHelpers.respondWithJson(requests, expectedData);
                BookmarkHelpers.verifyBookmarkedData(bookmarksView, expectedData);

                expect(bookmarksView.$('.paging-footer span.current-page').text().trim()).toBe('2');
                expect(bookmarksView.$('.paging-header span').text().trim()).toBe('Showing 11-12 out of 12 total');
            });

            it('can navigate forward and backward', function() {
                var requests = AjaxHelpers.requests(this);
                var bookmarksView = createBookmarksView();
                var expectedData = BookmarkHelpers.createBookmarksData(
                    {
                        numBookmarksToCreate: 10,
                        count: 15,
                        num_pages: 2,
                        current_page: 1,
                        start: 0
                    }
                );
                bookmarksView.showBookmarks();
                BookmarkHelpers.verifyPaginationInfo(
                    requests,
                    bookmarksView,
                    expectedData,
                    '1',
                    'Showing 1-10 out of 15 total'
                );
                verifyRequestParams(
                    requests,
                    {
                        course_id: BookmarkHelpers.TEST_COURSE_ID,
                        fields: 'display_name,path',
                        page: '1',
                        page_size: '10'
                    }
                );

                bookmarksView.$('.paging-footer .next-page-link').click();
                expectedData = BookmarkHelpers.createBookmarksData(
                    {
                        numBookmarksToCreate: 5,
                        count: 15,
                        num_pages: 2,
                        current_page: 2,
                        start: 10
                    }
                );
                BookmarkHelpers.verifyPaginationInfo(
                    requests,
                    bookmarksView,
                    expectedData,
                    '2',
                    'Showing 11-15 out of 15 total'
                );
                verifyRequestParams(
                    requests,
                    {
                        course_id: BookmarkHelpers.TEST_COURSE_ID,
                        fields: 'display_name,path',
                        page: '2',
                        page_size: '10'
                    }
                );

                expectedData = BookmarkHelpers.createBookmarksData(
                    {
                        numBookmarksToCreate: 10,
                        count: 15,
                        num_pages: 2,
                        current_page: 1,
                        start: 0
                    }
                );
                bookmarksView.$('.paging-footer .previous-page-link').click();
                BookmarkHelpers.verifyPaginationInfo(
                    requests,
                    bookmarksView,
                    expectedData,
                    '1',
                    'Showing 1-10 out of 15 total'
                );
                verifyRequestParams(
                    requests,
                    {
                        course_id: BookmarkHelpers.TEST_COURSE_ID,
                        fields: 'display_name,path',
                        page: '1',
                        page_size: '10'
                    }
                );
            });

            xit('can navigate to correct url', function() {
                var requests = AjaxHelpers.requests(this);
                var bookmarksView = createBookmarksView();
                var url;
                spyOn(bookmarksView, 'visitBookmark');
                bookmarksView.showBookmarks();
                AjaxHelpers.respondWithJson(requests, BookmarkHelpers.createBookmarksData({numBookmarksToCreate: 1}));

                bookmarksView.$('.bookmarks-results-list-item').click();
                url = bookmarksView.$('.bookmarks-results-list-item').attr('href');
                expect(bookmarksView.visitBookmark).toHaveBeenCalledWithUrl(url);
            });

            it('shows an error message for HTTP 500', function() {
                var requests = AjaxHelpers.requests(this);
                var bookmarksView = createBookmarksView();
                bookmarksView.showBookmarks();
                AjaxHelpers.respondWithError(requests);

                expect($('#error-message').text().trim()).toBe(bookmarksView.errorMessage);
            });
        });
    });
