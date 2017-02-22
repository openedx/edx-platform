define(['js/utils/module'],
    function(ModuleUtils) {
        describe('urlRoot ', function() {
            it('defines xblock urlRoot', function() {
                expect(ModuleUtils.urlRoot).toBe('/xblock');
            });
        });
        describe('getUpdateUrl ', function() {
            it('can take no arguments', function() {
                expect(ModuleUtils.getUpdateUrl()).toBe('/xblock/');
            });
            it('appends a locator', function() {
                expect(ModuleUtils.getUpdateUrl('locator')).toBe('/xblock/locator');
            });
        });
    }
);
