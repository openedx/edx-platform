define([
    'jquery', 'common/js/spec_helpers/template_helpers', 'js/discovery/models/filter',
    'js/discovery/views/filter_label'
], function($, TemplateHelpers, Filter, FilterLabel) {
    'use strict';

    describe('discovery.views.FilterLabel', function() {
        beforeEach(function() {
            TemplateHelpers.installTemplate('templates/discovery/filter');
            var filter = new Filter({
                type: 'language',
                query: 'en',
                name: 'English'
            });
            this.view = new FilterLabel({model: filter});
            this.view.render();
        });

        it('renders', function() {
            var data = this.view.model.attributes;
            expect(this.view.$el.find('button')).toHaveData('value', 'en');
            expect(this.view.$el.find('button')).toHaveData('type', 'language');
            expect(this.view.$el).toContainHtml(data.name);
        });

        it('renders changes', function() {
            this.view.model.set('query', 'es');
            expect(this.view.$el.find('button')).toHaveData('value', 'es');
        });

        it('removes itself', function() {
            // simulate removing from collection
            this.view.model.trigger('remove');
            expect(this.view.$el).not.toExist();
        });
    });
});
