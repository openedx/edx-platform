define(['js/discovery/models/facet_option'], function(FacetOption) {
    'use strict';

    describe('discovery.models.FacetOption', function () {

        beforeEach(function () {
            this.filter = new FacetOption();
        });

        it('has properties', function () {
            expect(this.filter.get('facet')).toBeDefined();
            expect(this.filter.get('term')).toBeDefined();
            expect(this.filter.get('count')).toBeDefined();
            expect(this.filter.get('selected')).toBeDefined();
        });

    });

});
