(function() {
    'use strict';

    describe('XBlock.Runtime.v1', function() {
        beforeEach(function() {
            setFixtures('<div class="xblock" data-handler-prefix="/xblock/fake-usage-id/handler"/>');
            this.children = [
                {
                    name: 'childA'
                }, {
                    name: 'childB'
                }
            ];
            this.element = $('.xblock')[0];
            $(this.element).prop('xblock_children', this.children);
            this.runtime = new XBlock.Runtime.v1(this.element);
        });

        it('provides a list of children', function() {
            expect(this.runtime.children(this.element)).toBe(this.children);
        });

        it('maps children by name', function() {
            expect(this.runtime.childMap(this.element, 'childA')).toBe(this.children[0]);
            expect(this.runtime.childMap(this.element, 'childB')).toBe(this.children[1]);
        });
    });
}).call(this);
