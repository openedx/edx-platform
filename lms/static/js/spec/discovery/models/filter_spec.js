define(['js/discovery/models/filter'], function(Filter) {
    'use strict';

    describe('discovery.models.Filter', function() {
        beforeEach(function() {
            this.filter = new Filter();
        });

        it('has properties', function() {
            expect(this.filter.get('type')).toBeDefined();
            expect(this.filter.get('query')).toBeDefined();
            expect(this.filter.get('name')).toBeDefined();
        });
    });
});
