define([
    'jquery', 'common/js/spec_helpers/template_helpers', 'js/discovery/collections/filters',
    'js/discovery/views/filter_bar'
], function($, TemplateHelpers, Filters, FilterBar) {
    'use strict';

    describe('discovery.views.FilterBar', function () {

        beforeEach(function () {
            loadFixtures('js/fixtures/discovery.html');
            TemplateHelpers.installTemplates([
                'templates/discovery/filter',
                'templates/discovery/filter_bar'
            ]);
            this.filters = new Filters();
            this.filterBar = new FilterBar({ collection: this.filters });
            this.filters.add({
                type: 'org',
                query: 'edX',
                name: 'edX'
            });
        });

        it('adds filter', function () {
            expect(this.filterBar.$el.find('button')).toHaveData('type', 'org');
        });

        it('removes filter', function () {
            this.filters.remove('org');
            expect(this.filterBar.$el.find('ul')).toBeEmpty();
            expect(this.filterBar.$el).toHaveClass('is-collapsed');
        });

        it('resets filters', function () {
            this.filters.reset();
            expect(this.filterBar.$el.find('ul')).toBeEmpty();
            expect(this.filterBar.$el).toHaveClass('is-collapsed');
        });

        it('triggers events', function () {
            this.onClearFilter = jasmine.createSpy('onClearFilter');
            this.onClearAll = jasmine.createSpy('onClearAll');
            this.filterBar.on('clearFilter', this.onClearFilter);
            this.filterBar.on('clearAll', this.onClearAll);
            this.filterBar.$el.find('button').click();
            expect(this.onClearFilter).toHaveBeenCalledWith('org');
            this.filterBar.$el.find('#clear-all-filters').click();
            expect(this.onClearAll).toHaveBeenCalled();
        });

    });

});
