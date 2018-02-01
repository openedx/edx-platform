/* globals loadFixtures */

import $ from 'jquery';
import _ from 'underscore';
import Logger from 'logger';
import URI from 'URIjs';
import AjaxHelpers from 'edx-ui-toolkit/js/utils/spec-helpers/ajax-helpers';
import TemplateHelpers from 'common/js/spec_helpers/template_helpers';
import MessageBannerView from 'js/views/message_banner';
import BookmarkHelpers from 'course_bookmarks/js/spec_helpers/bookmark_helpers';
import BookmarksListView from 'course_bookmarks/js/views/bookmarks_list';
import BookmarksCollection from 'course_bookmarks/js/collections/bookmarks';

function BookmarksListViewSpec() {
  'use strict';

  describe('BookmarksListView', () => {
    beforeEach(() => {
      loadFixtures('course_bookmarks/fixtures/bookmarks.html');
      TemplateHelpers.installTemplates([
        'templates/fields/message_banner',
      ]);
      spyOn(Logger, 'log').and.returnValue($.Deferred().resolve());
      jasmine.addMatchers({
        toHaveBeenCalledWithUrl() {
          return {
            compare(actual, expectedUrl) {
              return {
                pass: expectedUrl === actual.calls.mostRecent().args[0].currentTarget.pathname,
              };
            },
          };
        },
      });
    });

    const createBookmarksView = () => {
      const bookmarksCollection = new BookmarksCollection(
                    [],
        {
          course_id: BookmarkHelpers.TEST_COURSE_ID,
          url: BookmarkHelpers.TEST_API_URL,
        },
                );
      const bookmarksView = new BookmarksListView({
        $el: $('.course-bookmarks'),
        collection: bookmarksCollection,
        loadingMessageView: new MessageBannerView({ el: $('#loading-message') }),
        errorMessageView: new MessageBannerView({ el: $('#error-message') }),
      });
      return bookmarksView;
    };

    const verifyRequestParams = (requests, params) => {
      const urlParams = (new URI(requests[requests.length - 1].url)).query(true);
      _.each(params, (value, key) => {
        expect(urlParams[key]).toBe(value);
      });
    };

    it('can correctly render an empty bookmarks list', () => {
      const requests = AjaxHelpers.requests(this);
      const bookmarksView = createBookmarksView();
      const expectedData = BookmarkHelpers.createBookmarksData({ numBookmarksToCreate: 0 });

      bookmarksView.showBookmarks();
      AjaxHelpers.respondWithJson(requests, expectedData);

      expect(bookmarksView.$('.bookmarks-empty-header').text().trim()).toBe(
                    'You have not bookmarked any courseware pages yet',
                );

      expect(bookmarksView.$('.bookmarks-empty-detail-title').text().trim()).toBe(
                    'Use bookmarks to help you easily return to courseware pages. ' +
                    'To bookmark a page, click "Bookmark this page" under the page title.',
                );

      expect(bookmarksView.$('.paging-header').length).toBe(0);
      expect(bookmarksView.$('.paging-footer').length).toBe(0);
    });

    it('has rendered bookmarked list correctly', () => {
      const requests = AjaxHelpers.requests(this);
      const bookmarksView = createBookmarksView();
      const expectedData = BookmarkHelpers.createBookmarksData({ numBookmarksToCreate: 3 });

      bookmarksView.showBookmarks();
      verifyRequestParams(
                    requests,
        {
          course_id: BookmarkHelpers.TEST_COURSE_ID,
          fields: 'display_name,path',
          page: '1',
          page_size: '10',
        },
                );
      AjaxHelpers.respondWithJson(requests, expectedData);

      BookmarkHelpers.verifyBookmarkedData(bookmarksView, expectedData);

      expect(bookmarksView.$('.paging-header').length).toBe(1);
      expect(bookmarksView.$('.paging-footer').length).toBe(1);
    });

    it('calls bookmarks list render on page_changed event', () => {
      const renderSpy = spyOn(BookmarksListView.prototype, 'render');
      const listView = new BookmarksListView({
        collection: new BookmarksCollection([], {
          course_id: 'abc',
          url: '/test-bookmarks/url/',
        }),
      });
      listView.collection.trigger('page_changed');
      expect(renderSpy).toHaveBeenCalled();
    });

    it('can go to a page number', () => {
      const requests = AjaxHelpers.requests(this);
      let expectedData = BookmarkHelpers.createBookmarksData(
        {
          numBookmarksToCreate: 10,
          count: 12,
          num_pages: 2,
          current_page: 1,
          start: 0,
        },
                );
      const bookmarksView = createBookmarksView();
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
          start: 10,
        },
                );
      AjaxHelpers.respondWithJson(requests, expectedData);
      BookmarkHelpers.verifyBookmarkedData(bookmarksView, expectedData);

      expect(bookmarksView.$('.paging-footer span.current-page').text().trim()).toBe('2');
      expect(bookmarksView.$('.paging-header span').text().trim()).toBe('Showing 11-12 out of 12 total');
    });

    it('can navigate forward and backward', () => {
      const requests = AjaxHelpers.requests(this);
      const bookmarksView = createBookmarksView();
      let expectedData = BookmarkHelpers.createBookmarksData(
        {
          numBookmarksToCreate: 10,
          count: 15,
          num_pages: 2,
          current_page: 1,
          start: 0,
        },
                );
      bookmarksView.showBookmarks();
      BookmarkHelpers.verifyPaginationInfo(
                    requests,
                    bookmarksView,
                    expectedData,
                    '1',
                    'Showing 1-10 out of 15 total',
                );
      verifyRequestParams(
                    requests,
        {
          course_id: BookmarkHelpers.TEST_COURSE_ID,
          fields: 'display_name,path',
          page: '1',
          page_size: '10',
        },
                );

      bookmarksView.$('.paging-footer .next-page-link').click();
      expectedData = BookmarkHelpers.createBookmarksData(
        {
          numBookmarksToCreate: 5,
          count: 15,
          num_pages: 2,
          current_page: 2,
          start: 10,
        },
                );
      BookmarkHelpers.verifyPaginationInfo(
                    requests,
                    bookmarksView,
                    expectedData,
                    '2',
                    'Showing 11-15 out of 15 total',
                );
      verifyRequestParams(
                    requests,
        {
          course_id: BookmarkHelpers.TEST_COURSE_ID,
          fields: 'display_name,path',
          page: '2',
          page_size: '10',
        },
                );

      expectedData = BookmarkHelpers.createBookmarksData(
        {
          numBookmarksToCreate: 10,
          count: 15,
          num_pages: 2,
          current_page: 1,
          start: 0,
        },
                );
      bookmarksView.$('.paging-footer .previous-page-link').click();
      BookmarkHelpers.verifyPaginationInfo(
                    requests,
                    bookmarksView,
                    expectedData,
                    '1',
                    'Showing 1-10 out of 15 total',
                );
      verifyRequestParams(
                    requests,
        {
          course_id: BookmarkHelpers.TEST_COURSE_ID,
          fields: 'display_name,path',
          page: '1',
          page_size: '10',
        },
                );
    });

    xit('can navigate to correct url', () => {
      const requests = AjaxHelpers.requests(this);
      const bookmarksView = createBookmarksView();
      spyOn(bookmarksView, 'visitBookmark');
      bookmarksView.showBookmarks();
      AjaxHelpers.respondWithJson(
        requests,
        BookmarkHelpers.createBookmarksData({ numBookmarksToCreate: 1 }),
      );

      bookmarksView.$('.bookmarks-results-list-item').click();
      const url = bookmarksView.$('.bookmarks-results-list-item').attr('href');
      expect(bookmarksView.visitBookmark).toHaveBeenCalledWithUrl(url);
    });

    it('shows an error message for HTTP 500', () => {
      const requests = AjaxHelpers.requests(this);
      const bookmarksView = createBookmarksView();
      bookmarksView.showBookmarks();
      AjaxHelpers.respondWithError(requests);

      expect($('#error-message').text().trim()).toBe(bookmarksView.errorMessage);
    });
  });
}

export default BookmarksListViewSpec;
