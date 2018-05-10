define([
    'jquery',
    'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers',
    'course_bookmarks/js/spec_helpers/bookmark_helpers',
    'course_bookmarks/js/course_bookmarks_factory'
],
    function($, AjaxHelpers, BookmarkHelpers, CourseBookmarksFactory) {
        'use strict';

        describe('CourseBookmarksFactory', function() {
            beforeEach(function() {
                loadFixtures('course_bookmarks/fixtures/bookmarks.html');
            });

            it('can render the initial bookmarks', function() {
                var requests = AjaxHelpers.requests(this),
                    expectedData = BookmarkHelpers.createBookmarksData(
                        {
                            numBookmarksToCreate: 10,
                            count: 15,
                            num_pages: 2,
                            current_page: 1,
                            start: 0
                        }
                    ),
                    bookmarksView;
                bookmarksView = CourseBookmarksFactory({
                    $el: $('.course-bookmarks'),
                    courseId: BookmarkHelpers.TEST_COURSE_ID,
                    bookmarksApiUrl: BookmarkHelpers.TEST_API_URL
                });
                BookmarkHelpers.verifyPaginationInfo(
                    requests, bookmarksView, expectedData, '1', 'Showing 1-10 out of 15 total'
                );
            });
        });
    });
