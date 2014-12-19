define([
    'jquery',
    'js/common_helpers/template_helpers',
    'js/search/views/form',
    'js/search/views/item',
    'js/search/models/result'
],
function($, TemplateHelpers) {
    'use strict';


    describe('edx.search.Form', function () {

        beforeEach(function () {
            loadFixtures('js/fixtures/search_form.html');
            this.form = new edx.search.Form();
            this.onClear = jasmine.createSpy('onClear');
            this.onSearch = jasmine.createSpy('onSearch');
            this.form.on('clear', this.onClear);
            this.form.on('search', this.onSearch);
        });

        it('prevents default action on submit', function () {
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

        it('clears search when clicking on cancel button', function () {
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


    describe('edx.search.Item', function () {

        beforeEach(function () {
            TemplateHelpers.installTemplate('templates/courseware_search/search_item');
            this.model = {
                attributes: {
                    location: {
                        '0': 'section',
                        '1': 'subsection',
                        '2': 'unit'
                    },
                    content_type: 'Video',
                    excerpt: 'A short excerpt.',
                    url: 'path/to/content'
                }
            };
            this.item = new edx.search.Item({ model: this.model });
        });

        it('has useful html attributes', function () {
            expect(this.item.$el).toHaveAttr('role', 'region');
            expect(this.item.$el).toHaveAttr('aria-label', 'search result');
        });

        it('renders underscore template', function () {
            var href = this.model.attributes.url;
            var breadcrumbs = 'section ▸ subsection ▸ unit';

            this.item.render();
            expect(this.item.$el).toContainText(this.model.attributes.content_type);
            expect(this.item.$el).toContainText(this.model.attributes.excerpt);
            expect(this.item.$el.find('a[href="'+href+'"]')).toHaveAttr('href', href);
            expect(this.item.$el).toContainText(breadcrumbs);
        });

    });


    describe('edx.search.Result', function () {

        beforeEach(function () {
            this.result = new edx.search.Result();
        });

        it('has properties', function () {
            expect(this.result.get('location')).toBeDefined();
            expect(this.result.get('content_type')).toBeDefined();
            expect(this.result.get('excerpt')).toBeDefined();
            expect(this.result.get('url')).toBeDefined();
        });

    });

});
