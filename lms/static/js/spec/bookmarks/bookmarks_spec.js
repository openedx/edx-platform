define(['backbone', 'jquery', 'underscore', 'js/common_helpers/ajax_helpers', 'js/common_helpers/template_helpers',
        'js/bookmarks/models/bookmark',
        'js/bookmarks/collections/bookmarks',
        'js/bookmarks/views/bookmarks_button',
        'js/bookmarks/views/bookmarks_list'
       ],
    function (Backbone, $, _, AjaxHelpers, TemplateHelpers, BookmarksModel, BookmarksCollection, BookmarksButtonView,
              BookmarksResultsView) {
        'use strict';

        describe("edx.lms.bookmarks", function () {

            beforeEach(function () {
                setFixtures('<div class="courseware-bookmarks-button"></div><section id="courseware-results-list"></section>');
                TemplateHelpers.installTemplates(
                    [
                        'templates/bookmarks/bookmarks_button',
                        'templates/bookmarks/bookmarks_list'
                    ]
                );
            });

            describe("Bookmarks Button View", function () {
                var bookmarksButtonView;

                //beforeEach(function () {
                //    bookmarksButtonView = new BookmarksButtonView({});
                //
                //    var show = true;
                //    var fakeBookmarksShown = function () {
                //        show = !show;
                //        return show;
                //    };
                //
                //    spyOn(bookmarksButtonView.bookmarksResultsView, 'bookmarksShown').andCallFake(fakeBookmarksShown);
                //
                //    bookmarksButtonView.render();
                //});

                it("triggers the callback when bookmarks button is clicked", function () {
                    //
                    //spyOn(bookmarksButtonView, 'toggleBookmarksListView').andCallThrough();
                    //spyOn(bookmarksButtonView.bookmarksResultsView, 'loadBookmarks').andReturn(true);
                    //
                    //expect(bookmarksButtonView.$('.bookmarks-button')).toHaveAttr('aria-pressed', 'false');
                    //expect(bookmarksButtonView.$('.bookmarks-button')).toHaveClass('is-inactive');
                    //
                    //bookmarksButtonView.$('.bookmarks-button').click();
                    //expect(bookmarksButtonView.toggleBookmarksListView).toHaveBeenCalled();
                    //expect(bookmarksButtonView.$('.bookmarks-button')).toHaveAttr('aria-pressed', 'true');
                    //expect(bookmarksButtonView.$('.bookmarks-button')).toHaveClass('is-active');
                    //
                    //bookmarksButtonView.$('.bookmarks-button').click();
                    //expect(bookmarksButtonView.$('.bookmarks-button')).toHaveAttr('aria-pressed', 'false');
                    //expect(bookmarksButtonView.$('.bookmarks-button')).toHaveClass('is-inactive');
                });

                it("show triggers the bookmarks list view methods when bookmarks button is clicked", function () {
                    //spyOn(bookmarksButtonView.bookmarksResultsView, 'loadBookmarks');
                    //spyOn(bookmarksButtonView.bookmarksResultsView, 'hideBookmarks');
                    //
                    //bookmarksButtonView.$('.bookmarks-button').click();
                    //expect(bookmarksButtonView.toggleBookmarksListView.loadBookmarks).toHaveBeenCalled();
                    //
                    //bookmarksButtonView.$('.bookmarks-button').click();
                    //expect(bookmarksButtonView.toggleBookmarksListView.hideBookmarks).toHaveBeenCalled();
                });
            });
        });
    });
