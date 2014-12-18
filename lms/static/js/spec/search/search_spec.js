define([
    'jquery',
    'js/search/views/form',
    ], function() {
    describe('edx.search.Form spec', function() {
        'use strict';

        beforeEach(function() {
            loadFixtures('js/fixtures/search_form.html');
            this.form = new edx.search.Form();
            this.onClear = jasmine.createSpy('onClear');
            this.onSearch = jasmine.createSpy('onSearch');
            this.form.on('clear', this.onClear);
            this.form.on('search', this.onSearch);
        });

        it('prevents default action on submit', function() {
            expect(this.form.submitForm()).toEqual(false);
        });

        it('triggers a search event and changes to active state', function () {
            var term = 'search string';
            $('.search-field').val(term);
            $('form').trigger('submit');
            expect(this.onSearch).toHaveBeenCalledWith(term);
            expect($('.search-field')).toHaveClass('is-active');
            expect($('.search-button')).not.toBeVisible();
            expect($('.cancel-button')).toBeVisible();
        });

        it('clears search when clicking on cancel button', function() {
            $('.search-field').val('search string');
            $('.cancel-button').trigger('click');
            expect($('.search-field')).not.toHaveClass('is-active');
            expect($('.search-button')).toBeVisible();
            expect($('.cancel-button')).not.toBeVisible();
            expect($('.search-field')).toHaveValue('');
        });

        it('clears search when search box is empty', function() {
            $('.search-field').val('');
            $('form').trigger('submit');
            expect(this.onClear).toHaveBeenCalled();
            expect($('.search-field')).not.toHaveClass('is-active');
            expect($('.cancel-button')).not.toBeVisible();
            expect($('.search-button')).toBeVisible();
        });

    });

});
