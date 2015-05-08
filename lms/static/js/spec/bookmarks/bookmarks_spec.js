define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/bookmarks/collections/bookmarks',
        'js/bookmarks/models/bookmark',
        'js/bookmarks/views/bookmarks_button',
        'js/bookmarks/views/bookmarks_results'
       ],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, BookmarksCollection, BookmarksModel, BookmarksButtonView,
              BookmarksResultsView) {
        'use strict';

        describe("lms.courseware.bookmarks", function () {

            beforeEach(function () {
                setFixtures('<div class="courseware-bookmarks-button"></div><section id="courseware-search-results"></section>');
                TemplateHelpers.installTemplates(
                    [
                        'templates/bookmarks/bookmarks_button',
                        'templates/bookmarks/bookmarks_results'
                    ]
                );
            });

            describe("BookmarksButtonView", function () {

                it("works as expected", function () {

                    var show = true;
                    var fakeBookmarksShown = function () {
                        show = !show;
                        return show;
                    };

                    var bookmarksButtonView = new BookmarksButtonView({});
                    spyOn(bookmarksButtonView, 'toggleBookmarksListView').andCallThrough();
                    spyOn(bookmarksButtonView.bookmarksResultsView, 'loadBookmarks').andReturn(true);
                    spyOn(bookmarksButtonView.bookmarksResultsView, 'bookmarksShown').andCallFake(fakeBookmarksShown);
                    bookmarksButtonView.render();

                    expect(bookmarksButtonView.$('.bookmarks-button').attr('aria-pressed')).toBe("false");

                    bookmarksButtonView.$('.bookmarks-button').click();
                    expect(bookmarksButtonView.toggleBookmarksListView).toHaveBeenCalled();
                    expect(bookmarksButtonView.$('.bookmarks-button').attr('aria-pressed')).toBe("true");

                    bookmarksButtonView.$('.bookmarks-button').click();
                    expect(bookmarksButtonView.$('.bookmarks-button').attr('aria-pressed')).toBe("false");
                });
            });

            describe("BookmarksResultsView", function () {

            });
        });
    });
