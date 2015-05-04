define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/bookmarks/views/bookmarks_button'
       ],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, BookmarksButtonView) {
        'use strict';

        describe("lms.courseware.bookmarks", function () {

            var bookmarksButtonView;
            var BOOKMARKS_API_URL = '/api/bookmarks/v0/bookmarks/';

            beforeEach(function () {
                loadFixtures('js/fixtures/bookmarks/bookmarks.html');
                TemplateHelpers.installTemplates(
                    [
                        'templates/message_view',
                        'templates/bookmarks/bookmarks_list'
                    ]
                );

                bookmarksButtonView = new BookmarksButtonView();

                this.addMatchers({
                   toHaveBeenCalledWithUrl: function (expectedUrl) {
                       return expectedUrl === this.actual.argsForCall[0][0].target.pathname;
                   }
                });
            });

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

                for(var b = 0; b < results.length; b++) {
                    courseId = results[b].course_id;
                    usageId = results[b].usage_id;

                    expect(bookmarks[b]).toHaveAttr('href', createBookmarkUrl(courseId, usageId));

                    expect($(bookmarks[b]).find('.list-item-breadcrumbtrail').html().trim()).
                        toBe(breadcrumbTrail(results[b].path, results[b].display_name));

                    expect($(bookmarks[b]).find('.list-item-date').text().trim()).
                        toBe('Bookmarked on ' + view.humanFriendlyDate(results[b].created));
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
            });

            it("has rendered bookmarked list correctly", function () {
                var requests = AjaxHelpers.requests(this);
                var url = BOOKMARKS_API_URL + '?course_id=COURSE_ID&fields=display_name%2Cpath';
                var expectedData = createBookmarksData(3);

                spyOn(bookmarksButtonView.bookmarksListView, 'courseId').andReturn('COURSE_ID');
                bookmarksButtonView.$('.bookmarks-list-button').click();
                expect($('#loading-message').text().trim()).
                    toBe(bookmarksButtonView.bookmarksListView.loadingMessage);

                AjaxHelpers.expectRequest(requests, 'GET', url);
                AjaxHelpers.respondWithJson(requests, expectedData);

                expect(bookmarksButtonView.bookmarksListView.$('.bookmarks-results-header').text().trim()).
                    toBe('My Bookmarks');

                verifyBookmarkedData(bookmarksButtonView.bookmarksListView, expectedData);
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
