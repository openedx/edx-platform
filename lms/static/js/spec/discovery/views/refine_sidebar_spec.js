define([
    'jquery', 'common/js/spec_helpers/template_helpers', 'js/discovery/models/facet_option',
    'js/discovery/views/refine_sidebar'
], function($, TemplateHelpers, FacetOption, RefineSidebar) {
    'use strict';

    var MEANINGS = {
        org: {
            name: 'Organization',
            terms: {
                edX1: 'edX_1'
            }
        },
        modes: {
            name: 'Course Type',
            terms: {
                honor: 'Honor',
                verified: 'Verified'
            }
        },
        language: {
            terms: {
                en: 'English',
                hr: 'Croatian'
            }
        }
    };


    describe('discovery.views.RefineSidebar', function() {
        beforeEach(function() {
            loadFixtures('js/fixtures/discovery.html');
            TemplateHelpers.installTemplates([
                'templates/discovery/facet',
                'templates/discovery/facet_option'
            ]);
            this.facetOptions = new Backbone.Collection([], {model: FacetOption});
            this.facetOptions.add([
                {facet: 'language', term: 'es', count: 12},
                {facet: 'language', term: 'en', count: 10},
                {facet: 'modes', term: 'honor', count: 2, selected: true}
            ]);
            this.sidebar = new RefineSidebar({collection: this.facetOptions, meanings: MEANINGS});
            this.sidebar.render();
        });

        it('styles active filter', function() {
            expect(this.sidebar.$el.find('button.selected')).toHaveData('facet', 'modes');
        });

        it('styles active filter', function() {
            this.onSelect = jasmine.createSpy('onSelect');
            this.sidebar.on('selectOption', this.onSelect);
            this.sidebar.$el.find('button[data-value="en"]').click();
            expect(this.onSelect).toHaveBeenCalledWith('language', 'en', 'English');
        });

        it('expands and collapses facet', function() {
            var options = _.range(20).map(function(number) {
                return {facet: 'org', term: 'test' + number, count: 1};
            });
            this.facetOptions.reset(options);
            this.sidebar.render();
            this.sidebar.$el.find('.show-more').click();
            expect(this.sidebar.$el.find('ul.facet-list')).not.toHaveClass('collapse');
            expect(this.sidebar.$el.find('.show-more')).toHaveClass('hidden');
            this.sidebar.$el.find('.show-less').click();
            expect(this.sidebar.$el.find('ul.facet-list')).toHaveClass('collapse');
            expect(this.sidebar.$el.find('.show-less')).toHaveClass('hidden');
        });
    });
});

