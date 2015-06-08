define([
    'jquery', 'underscore', 'common/js/spec_helpers/template_helpers', 'common/js/spec_helpers/ajax_helpers',
    'logger', 'js/edxnotes/collections/tabs', 'js/edxnotes/views/tabs/search_results',
    'js/spec/edxnotes/custom_matchers', 'jasmine-jquery'
], function(
    $, _, TemplateHelpers, AjaxHelpers, Logger, TabsCollection, SearchResultsView,
    customMatchers
) {
    'use strict';
    describe('EdxNotes SearchResultsView', function() {
        var notes = [
            {
                created: 'December 11, 2014 at 11:12AM',
                updated: 'December 11, 2014 at 11:12AM',
                text: 'Third added model',
                quote: 'Should be listed first'
            },
            {
                created: 'December 11, 2014 at 11:11AM',
                updated: 'December 11, 2014 at 11:11AM',
                text: 'Second added model',
                quote: 'Should be listed second'
            },
            {
                created: 'December 11, 2014 at 11:10AM',
                updated: 'December 11, 2014 at 11:10AM',
                text: 'First added model',
                quote: 'Should be listed third'
            }
        ],
        responseJson = {
            total: 3,
            rows: notes
        },
        getView, submitForm;

        getView = function (tabsCollection, options) {
            options = _.defaults(options || {}, {
                el: $('.wrapper-student-notes'),
                tabsCollection: tabsCollection,
                user: 'test_user',
                courseId: 'course_id',
                createTabOnInitialization: false
            });
            return new SearchResultsView(options);
        };

        submitForm = function (searchBox, text) {
            searchBox.$('.search-notes-input').val(text);
            searchBox.$('.search-notes-submit').click();
        };

        beforeEach(function () {
            customMatchers(this);
            loadFixtures('js/fixtures/edxnotes/edxnotes.html');
            TemplateHelpers.installTemplates([
                'templates/edxnotes/note-item', 'templates/edxnotes/tab-item'
            ]);

            this.tabsCollection = new TabsCollection();
        });

        it('does not create a tab and content on initialization', function () {
            var view = getView(this.tabsCollection);
            expect(this.tabsCollection).toHaveLength(0);
            expect(view.$('#search-results-panel')).not.toExist();
        });

        it('displays a tab and content on search with proper data and order', function () {
            var view = getView(this.tabsCollection),
                requests = AjaxHelpers.requests(this);

            submitForm(view.searchBox, 'second');
            AjaxHelpers.respondWithJson(requests, responseJson);

            expect(this.tabsCollection).toHaveLength(1);
            expect(this.tabsCollection.at(0).toJSON()).toEqual({
                name: 'Search Results',
                identifier: 'view-search-results',
                icon: 'fa fa-search',
                is_active: true,
                is_closable: true,
                view: 'Search Results'
            });
            expect(view.$('#search-results-panel')).toExist();
            expect(view.$('#search-results-panel')).toBeFocused();
            expect(view.$('.note')).toHaveLength(3);
            view.searchResults.collection.each(function (model, index) {
                expect(model.get('text')).toBe(notes[index].text);
            });
        });

        it('displays loading indicator when search is running', function () {
            var view = getView(this.tabsCollection),
                requests = AjaxHelpers.requests(this);

            submitForm(view.searchBox, 'test query');
            expect(view.$('.ui-loading')).not.toHaveClass('is-hidden');
            expect(view.$('.ui-loading')).toBeFocused();
            expect(this.tabsCollection).toHaveLength(1);
            expect(view.searchResults).toBeNull();
            expect(view.$('.tab-panel')).not.toExist();
            AjaxHelpers.respondWithJson(requests, responseJson);
            expect(view.$('.ui-loading')).toHaveClass('is-hidden');
        });

        it('displays no results message', function () {
            var view = getView(this.tabsCollection),
                requests = AjaxHelpers.requests(this);

            submitForm(view.searchBox, 'some text');
            AjaxHelpers.respondWithJson(requests, {
                total: 0,
                rows: []
            });

            expect(view.$('#search-results-panel')).not.toExist();
            expect(view.$('#no-results-panel')).toBeFocused();
            expect(view.$('#no-results-panel')).toExist();
            expect(view.$('#no-results-panel')).toContainText(
                'No results found for "some text".'
            );
        });

        it('does not send an additional request on switching between tabs', function () {
            var view = getView(this.tabsCollection),
                requests = AjaxHelpers.requests(this);

            spyOn(Logger, 'log');
            submitForm(view.searchBox, 'test_query');
            AjaxHelpers.respondWithJson(requests, responseJson);

            expect(requests).toHaveLength(1);

            this.tabsCollection.add({});
            this.tabsCollection.at(1).activate();
            expect(view.$('#search-results-panel')).not.toExist();
            this.tabsCollection.at(0).activate();

            expect(requests).toHaveLength(1);
            expect(view.$('#search-results-panel')).toExist();
            expect(view.$('.note')).toHaveLength(3);
        });

        it('can clear search results if tab is closed', function () {
            var view = getView(this.tabsCollection),
                requests = AjaxHelpers.requests(this);

            submitForm(view.searchBox, 'test_query');
            AjaxHelpers.respondWithJson(requests, responseJson);
            expect(view.searchResults).toBeDefined();
            this.tabsCollection.at(0).destroy();
            expect(view.searchResults).toBeNull();
        });

        it('can correctly show/hide error messages', function () {
            var view = getView(this.tabsCollection),
                requests = AjaxHelpers.requests(this);

            submitForm(view.searchBox, 'test error');
            AjaxHelpers.respondWithError(requests, 500, {error: 'test error message'});

            expect(view.$('.wrapper-msg')).not.toHaveClass('is-hidden');
            expect(view.$('.wrapper-msg .copy')).toContainText('test error message');
            expect(view.$('.ui-loading')).toHaveClass('is-hidden');

            submitForm(view.searchBox, 'Second');
            AjaxHelpers.respondWithJson(requests, responseJson);

            expect(view.$('.wrapper-msg')).toHaveClass('is-hidden');
            expect(view.$('.wrapper-msg .copy')).toBeEmpty();
        });

        it('can correctly update search results', function () {
            var view = getView(this.tabsCollection),
                requests = AjaxHelpers.requests(this),
                newNotes = [{
                    created: 'December 11, 2014 at 11:10AM',
                    updated: 'December 11, 2014 at 11:10AM',
                    text: 'New Note',
                    quote: 'New Note'
                }];

            submitForm(view.searchBox, 'test_query');
            AjaxHelpers.respondWithJson(requests, responseJson);

            expect(view.$('.note')).toHaveLength(3);

            submitForm(view.searchBox, 'new_test_query');
            AjaxHelpers.respondWithJson(requests, {
                total: 1,
                rows: newNotes
            });

            expect(view.$('.note').length).toHaveLength(1);
            view.searchResults.collection.each(function (model, index) {
                expect(model.get('text')).toBe(newNotes[index].text);
            });
        });
    });
});
