define(['backbone', 'jquery', 'underscore',
        'js/bookmarks/collections/bookmarks',
        'js/bookmarks/models/bookmark',
        'js/bookmarks/views/bookmarks_button',
        'js/bookmarks/views/bookmarks_results'
       ],
    function (Backbone, $, _, BookmarksCollection, BookmarksModel, BookmarksButtonView, BookmarksResultsView) {
        'use strict';

        describe("lms.courseware.bookmarks", function () {

            beforeEach(function () {
                setFixtures('<div class="courseware-bookmarks-button"></div><section id="courseware-search-results"></section>');
                TemplateHelpers.installTemplate("templates/bookmarks/bookmarks_button");
                TemplateHelpers.installTemplate("templates/bookmarks/bookmarks_results");
            });

            describe("BookmarksButtonView", function () {

                it("works as expected", function () {
                    var bookmarksButtonView = new BookmarksButtonView({});
                    spyOn(bookmarksButtonView, 'toggleBookmarksListView');
                    bookmarksButtonView.render();

                    expect(bookmarksButtonView.$('.bookmarks-button').attr('aria-pressed')).toBe("false");

                    bookmarksButtonView.$('.bookmarks-button').click();

                    expect(bookmarksButtonView.toggleBookmarksListView).toHaveBeenCalled();
                });
            });

            describe("BookmarksResultsView", function () {

            });
        });
    });
