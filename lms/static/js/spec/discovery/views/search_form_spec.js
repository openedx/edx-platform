define(['jquery', 'js/discovery/views/search_form'], function($, SearchForm) {
    'use strict';

    describe('discovery.views.SearchForm', function() {
        beforeEach(function() {
            loadFixtures('js/fixtures/discovery.html');
            this.form = new SearchForm();
            this.onSearch = jasmine.createSpy('onSearch');
            this.form.on('search', this.onSearch);
        });

        it('trims input string', function() {
            var term = '  search string  ';
            $('.discovery-input').val(term);
            $('form').trigger('submit');
            expect(this.onSearch).toHaveBeenCalledWith($.trim(term));
        });

        it('handles calls to doSearch', function() {
            var term = '  search string  ';
            $('.discovery-input').val(term);
            this.form.doSearch(term);
            expect(this.onSearch).toHaveBeenCalledWith($.trim(term));
            expect($('.discovery-input').val()).toBe(term);
            expect($('#discovery-message')).toBeEmpty();
        });

        it('clears search', function() {
            $('.discovery-input').val('somethig');
            this.form.clearSearch();
            expect($('.discovery-input').val()).toBe('');
        });

        it('shows/hides loading indicator', function() {
            this.form.showLoadingIndicator();
            expect($('#loading-indicator')).not.toHaveClass('hidden');
            this.form.hideLoadingIndicator();
            expect($('#loading-indicator')).toHaveClass('hidden');
        });

        it('shows messages', function() {
            this.form.showFoundMessage(123);
            expect($('#discovery-message')).toContainHtml(123);
            this.form.showNotFoundMessage();
            expect($('#discovery-message')).not.toBeEmpty();
            this.form.showErrorMessage();
            expect($('#discovery-message')).not.toBeEmpty();
        });
    });
});
