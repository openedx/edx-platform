define(['backbone', 'jquery', 'underscore', 'logger', 'common/js/spec_helpers/ajax_helpers',
        'common/js/spec_helpers/template_helpers', 'js/bookmarks/views/bookmarks_list_button'
       ],
    function (Backbone, $, _, Logger, AjaxHelpers, TemplateHelpers, BookmarksListButtonView) {
        'use strict';

        describe("lms.courseware.bookmarks", function () {

            var bookmarksButtonView;
            var BOOKMARKS_API_URL = '/api/bookmarks/v1/bookmarks/';

            beforeEach(function () {
                loadFixtures('js/fixtures/bookmarks/bookmarks.html');
                TemplateHelpers.installTemplates(
                    [
                        'templates/message_view',
                        'templates/bookmarks/bookmarks_list'
                    ]
                );
                spyOn(Logger, 'log').andReturn($.Deferred().resolve());
                this.addMatchers({
                   toHaveBeenCalledWithUrl: function (expectedUrl) {
                       return expectedUrl === this.actual.argsForCall[0][0].target.pathname;
                   }
                });

                bookmarksButtonView = new BookmarksListButtonView();
            });

            var verifyUrl = function (requests) {
                var request = requests[0];

                expect(request.url).toContain(BOOKMARKS_API_URL);
                expect(request.url).toContain('course_id=a%2Fb%2F');
                expect(request.url).toContain('page_size=10');
                expect(request.url).toContain('fields=display_name%2Cpath');
            };

            var createBookmarksData = function (count) {
                var data = {
                    results: []
                };

                for(var i = 0; i < count; i++) {
                    var bookmarkInfo = {
                        id: i,
                        display_name: 'UNIT_DISPLAY_NAME_' + i,
                        created: new Date().toISOString(),
                        course_id: 'COURSE_ID',
                        usage_id: 'UNIT_USAGE_ID_' + i,
                        block_type: 'vertical',
                        path: [
                            {display_name: 'SECTION_DISAPLAY_NAME', usage_id: 'SECTION_USAGE_ID'},
                            {display_name: 'SUBSECTION_DISAPLAY_NAME', usage_id: 'SUBSECTION_USAGE_ID'}
                        ]
                    };

                    data.results.push(bookmarkInfo);
                }

                return data;
            };

            var createBookmarkUrl = function (courseId, usageId) {
                return '/courses/' + courseId + '/jump_to/' + usageId;
            };

            var breadcrumbTrail = function (path, unitDisplayName) {
                return _.pluck(path, 'display_name').
                    concat([unitDisplayName]).
                    join(' <i class="icon fa fa-caret-right" aria-hidden="true"></i><span class="sr">-</span> ');
            };

            var verifyBookmarkedData = function (view, expectedData) {
                var courseId, usageId;
                var bookmarks = view.$('.bookmarks-results-list-item');
                var results = expectedData.results;

                expect(bookmarks.length, results.length);

                for(var bookmark_index = 0; bookmark_index < results.length; bookmark_index++) {
                    courseId = results[bookmark_index].course_id;
                    usageId = results[bookmark_index].usage_id;

                    expect(bookmarks[bookmark_index]).toHaveAttr('href', createBookmarkUrl(courseId, usageId));

                    expect($(bookmarks[bookmark_index]).data('bookmarkId')).toBe(bookmark_index);
                    expect($(bookmarks[bookmark_index]).data('componentType')).toBe('vertical');
                    expect($(bookmarks[bookmark_index]).data('usageId')).toBe(usageId);

                    expect($(bookmarks[bookmark_index]).find('.list-item-breadcrumbtrail').html().trim()).
                        toBe(breadcrumbTrail(results[bookmark_index].path, results[bookmark_index].display_name));

                    expect($(bookmarks[bookmark_index]).find('.list-item-date').text().trim()).
                        toBe('Bookmarked on ' + view.humanFriendlyDate(results[bookmark_index].created));
                }
            };

            it("has correct behavior for bookmarks button", function () {
                var requests = AjaxHelpers.requests(this);

                spyOn(bookmarksButtonView, 'toggleBookmarksListView').andCallThrough();

                bookmarksButtonView.delegateEvents();

                expect(bookmarksButtonView.$('.bookmarks-list-button')).toHaveAttr('aria-pressed', 'false');
                expect(bookmarksButtonView.$('.bookmarks-list-button')).toHaveClass('is-inactive');

                bookmarksButtonView.$('.bookmarks-list-button').click();
                expect(bookmarksButtonView.toggleBookmarksListView).toHaveBeenCalled();
                expect(bookmarksButtonView.$('.bookmarks-list-button')).toHaveAttr('aria-pressed', 'true');
                expect(bookmarksButtonView.$('.bookmarks-list-button')).toHaveClass('is-active');
                AjaxHelpers.respondWithJson(requests, createBookmarksData(1));

                bookmarksButtonView.$('.bookmarks-list-button').click();
                expect(bookmarksButtonView.$('.bookmarks-list-button')).toHaveAttr('aria-pressed', 'false');
                expect(bookmarksButtonView.$('.bookmarks-list-button')).toHaveClass('is-inactive');
            });

            it("has rendered empty bookmarks list correctly", function () {
                var requests = AjaxHelpers.requests(this);
                var expectedData = createBookmarksData(0);

                bookmarksButtonView.$('.bookmarks-list-button').click();
                AjaxHelpers.respondWithJson(requests, expectedData);

                expect(bookmarksButtonView.bookmarksListView.$('.bookmarks-empty-header').text().trim()).
                    toBe('You have not bookmarked any courseware pages yet.');

                var emptyListText = "Use bookmarks to help you easily return to courseware pages. " +
                    "To bookmark a page, select Bookmark in the upper right corner of that page. " +
                    "To see a list of all your bookmarks, select Bookmarks in the upper left " +
                    "corner of any courseware page.";

                expect(bookmarksButtonView.bookmarksListView.$('.bookmarks-empty-detail-title').text().trim()).
                    toBe(emptyListText);

                expect(bookmarksButtonView.bookmarksListView.$('.paging-header').length).toBe(0);
                expect(bookmarksButtonView.bookmarksListView.$('.paging-footer').length).toBe(0);
            });

            it("has rendered bookmarked list correctly", function () {
                var requests = AjaxHelpers.requests(this);
                var expectedData = createBookmarksData(3);

                bookmarksButtonView.$('.bookmarks-list-button').click();
                expect($('#loading-message').text().trim()).
                    toBe(bookmarksButtonView.bookmarksListView.loadingMessage);

                verifyUrl(requests);
                AjaxHelpers.respondWithJson(requests, expectedData);

                expect(bookmarksButtonView.bookmarksListView.$('.bookmarks-results-header').text().trim()).
                    toBe('My Bookmarks');

                verifyBookmarkedData(bookmarksButtonView.bookmarksListView, expectedData);

                expect(bookmarksButtonView.bookmarksListView.$('.paging-header').length).toBe(1);
                expect(bookmarksButtonView.bookmarksListView.$('.paging-footer').length).toBe(1);
            });

            it("can navigate to correct url", function () {
                var requests = AjaxHelpers.requests(this);
                spyOn(bookmarksButtonView.bookmarksListView, 'visitBookmark');

                bookmarksButtonView.$('.bookmarks-list-button').click();
                AjaxHelpers.respondWithJson(requests, createBookmarksData(1));

                bookmarksButtonView.bookmarksListView.$('.bookmarks-results-list-item').click();
                var url = bookmarksButtonView.bookmarksListView.$('.bookmarks-results-list-item').attr('href');
                expect(bookmarksButtonView.bookmarksListView.visitBookmark).toHaveBeenCalledWithUrl(url);
            });

            it("shows an error message for HTTP 500", function () {
                var requests = AjaxHelpers.requests(this);

                bookmarksButtonView.$('.bookmarks-list-button').click();

                AjaxHelpers.respondWithError(requests);

                expect(bookmarksButtonView.bookmarksListView.$('.bookmarks-results-header').text().trim()).not
                    .toBe('My Bookmarks');
                expect($('#error-message').text().trim()).toBe(bookmarksButtonView.bookmarksListView.errorMessage);
            });
        });
    });
