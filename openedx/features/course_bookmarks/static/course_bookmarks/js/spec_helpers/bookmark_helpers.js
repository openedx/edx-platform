define(
    [
        'underscore',
        'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers'
    ],
    function(_, AjaxHelpers) {
        'use strict';

        var TEST_COURSE_ID = 'course-v1:test-course';

        var createBookmarksData = function(options) {
            var data = {
                    count: options.count || 0,
                    num_pages: options.num_pages || 1,
                    current_page: options.current_page || 1,
                    start: options.start || 0,
                    results: []
                },
                i, bookmarkInfo;

            for (i = 0; i < options.numBookmarksToCreate; i++) {
                bookmarkInfo = {
                    id: i,
                    display_name: 'UNIT_DISPLAY_NAME_' + i,
                    created: new Date().toISOString(),
                    course_id: 'COURSE_ID',
                    usage_id: 'UNIT_USAGE_ID_' + i,
                    block_type: 'vertical',
                    path: [
                        {display_name: 'SECTION_DISPLAY_NAME', usage_id: 'SECTION_USAGE_ID'},
                        {display_name: 'SUBSECTION_DISPLAY_NAME', usage_id: 'SUBSECTION_USAGE_ID'}
                    ]
                };

                data.results.push(bookmarkInfo);
            }

            return data;
        };

        var createBookmarkUrl = function(courseId, usageId) {
            return '/courses/' + courseId + '/jump_to/' + usageId;
        };

        var breadcrumbTrail = function(path, unitDisplayName) {
            return _.pluck(path, 'display_name').
            concat([unitDisplayName]).
            join(' <span class="icon fa fa-caret-right" aria-hidden="true"></span><span class="sr">-</span> ');
        };

        var verifyBookmarkedData = function(view, expectedData) {
            var courseId, usageId;
            var bookmarks = view.$('.bookmarks-results-list-item');
            var results = expectedData.results;
            var i, $bookmark;

            expect(bookmarks.length, results.length);

            for (i = 0; i < results.length; i++) {
                $bookmark = $(bookmarks[i]);
                courseId = results[i].course_id;
                usageId = results[i].usage_id;

                expect(bookmarks[i]).toHaveAttr('href', createBookmarkUrl(courseId, usageId));

                expect($bookmark.data('bookmarkId')).toBe(i);
                expect($bookmark.data('componentType')).toBe('vertical');
                expect($bookmark.data('usageId')).toBe(usageId);

                expect($bookmark.find('.list-item-breadcrumbtrail').html().trim())
                    .toBe(breadcrumbTrail(results[i].path, results[i].display_name));

                expect($bookmark.find('.list-item-date').text().trim())
                    .toBe('Bookmarked on ' + view.humanFriendlyDate(results[i].created));
            }
        };

        var verifyPaginationInfo = function(requests, view, expectedData, currentPage, headerMessage) {
            AjaxHelpers.respondWithJson(requests, expectedData);
            verifyBookmarkedData(view, expectedData);
            expect(view.$('.paging-footer span.current-page').text().trim()).toBe(currentPage);
            expect(view.$('.paging-header span').text().trim()).toBe(headerMessage);
        };

        return {
            TEST_COURSE_ID: TEST_COURSE_ID,
            TEST_API_URL: '/bookmarks/api',
            createBookmarksData: createBookmarksData,
            createBookmarkUrl: createBookmarkUrl,
            verifyBookmarkedData: verifyBookmarkedData,
            verifyPaginationInfo: verifyPaginationInfo
        };
    });
