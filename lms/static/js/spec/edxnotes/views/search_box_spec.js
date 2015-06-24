define([
    'jquery', 'underscore', 'common/js/spec_helpers/ajax_helpers', 'js/edxnotes/views/search_box',
    'js/edxnotes/collections/notes', 'js/spec/edxnotes/custom_matchers', 'jasmine-jquery'
], function($, _, AjaxHelpers, SearchBoxView, NotesCollection, customMatchers) {
    'use strict';
    describe('EdxNotes SearchBoxView', function() {
        var getSearchBox, submitForm, assertBoxIsEnabled, assertBoxIsDisabled;

        getSearchBox = function (options) {
            options = _.defaults(options || {}, {
                el: $('#search-notes-form').get(0),
                beforeSearchStart: jasmine.createSpy(),
                search: jasmine.createSpy(),
                error: jasmine.createSpy(),
                complete: jasmine.createSpy()
            });

            return new SearchBoxView(options);
        };

        submitForm = function (searchBox, text) {
            searchBox.$('.search-notes-input').val(text);
            searchBox.$('.search-notes-submit').click();
        };

        assertBoxIsEnabled = function (searchBox) {
            expect(searchBox.$el).not.toHaveClass('is-looking');
            expect(searchBox.$('.search-notes-submit')).not.toHaveClass('is-disabled');
            expect(searchBox.isDisabled).toBeFalsy();
        };

        assertBoxIsDisabled = function (searchBox) {
            expect(searchBox.$el).toHaveClass('is-looking');
            expect(searchBox.$('.search-notes-submit')).toHaveClass('is-disabled');
            expect(searchBox.isDisabled).toBeTruthy();
        };

        beforeEach(function () {
            customMatchers(this);
            loadFixtures('js/fixtures/edxnotes/edxnotes.html');
            spyOn(Logger, 'log');
            this.searchBox = getSearchBox();
        });

        it('sends a request with proper information on submit the form', function () {
            var requests = AjaxHelpers.requests(this),
                form = this.searchBox.el,
                request;

            submitForm(this.searchBox, 'test_text');
            request = requests[0];
            expect(request.method).toBe(form.method.toUpperCase());
            expect(request.url).toBe(form.action + '?' + $.param({text: 'test_text'}));
        });

        it('returns success result', function () {
            var requests = AjaxHelpers.requests(this);
            submitForm(this.searchBox, 'test_text');
            expect(this.searchBox.options.beforeSearchStart).toHaveBeenCalledWith(
                'test_text'
            );
            assertBoxIsDisabled(this.searchBox);
            AjaxHelpers.respondWithJson(requests, {
                total: 2,
                rows: [null, null]
            });
            assertBoxIsEnabled(this.searchBox);
            expect(this.searchBox.options.search).toHaveBeenCalledWith(
                jasmine.any(NotesCollection), 2, 'test_text'
            );
            expect(this.searchBox.options.complete).toHaveBeenCalledWith(
                'test_text'
            );
        });

        it('should log the edx.course.student_notes.searched event properly', function () {
            var requests = AjaxHelpers.requests(this);
            submitForm(this.searchBox, 'test_text');
            AjaxHelpers.respondWithJson(requests, {
                total: 2,
                rows: [null, null]
            });

            expect(Logger.log).toHaveBeenCalledWith('edx.course.student_notes.searched', {
                'number_of_results': 2,
                'search_string': 'test_text'
            });
        });

        it('returns default error message if received data structure is wrong', function () {
            var requests = AjaxHelpers.requests(this);
            submitForm(this.searchBox, 'test_text');
            AjaxHelpers.respondWithJson(requests, {});
            expect(this.searchBox.options.error).toHaveBeenCalledWith(
                'An error has occurred. Make sure that you are connected to the Internet, and then try refreshing the page.',
                'test_text'
            );
            expect(this.searchBox.options.complete).toHaveBeenCalledWith(
                'test_text'
            );
        });

        it('returns default error message if network error occurs', function () {
            var requests = AjaxHelpers.requests(this);
            submitForm(this.searchBox, 'test_text');
            AjaxHelpers.respondWithError(requests);
            expect(this.searchBox.options.error).toHaveBeenCalledWith(
                'An error has occurred. Make sure that you are connected to the Internet, and then try refreshing the page.',
                'test_text'
            );
            expect(this.searchBox.options.complete).toHaveBeenCalledWith(
                'test_text'
            );
        });

        it('returns error message if server error occurs', function () {
            var requests = AjaxHelpers.requests(this);
            submitForm(this.searchBox, 'test_text');
            assertBoxIsDisabled(this.searchBox);

            requests[0].respond(
                500, {'Content-Type': 'application/json'},
                JSON.stringify({
                    error: 'test error message'
                })
            );

            assertBoxIsEnabled(this.searchBox);
            expect(this.searchBox.options.error).toHaveBeenCalledWith(
                'test error message',
                'test_text'
            );
            expect(this.searchBox.options.complete).toHaveBeenCalledWith(
                'test_text'
            );
        });

        it('does not send second request during current search', function () {
            var requests = AjaxHelpers.requests(this);
            submitForm(this.searchBox, 'test_text');
            assertBoxIsDisabled(this.searchBox);
            submitForm(this.searchBox, 'another_text');
            AjaxHelpers.respondWithJson(requests, {
                total: 2,
                rows: [null, null]
            });
            assertBoxIsEnabled(this.searchBox);
            expect(requests).toHaveLength(1);
        });

        it('returns error message if the field is empty', function () {
            var requests = AjaxHelpers.requests(this);
            submitForm(this.searchBox, '   ');
            expect(requests).toHaveLength(0);
            assertBoxIsEnabled(this.searchBox);
            expect(this.searchBox.options.error).toHaveBeenCalledWith(
                'Please enter a term in the <a href="#search-notes-input"> search field</a>.',
                '   '
            );
        });
    });
});
