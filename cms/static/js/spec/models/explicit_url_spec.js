define(['js/models/explicit_url'],
    function(Model) {
        describe('Model ', function() {
            it('allows url to be passed in constructor', function() {
                expect(new Model({explicit_url: '/fancy/url'}).url()).toBe('/fancy/url');
            });
            it('returns empty string if url not set', function() {
                expect(new Model().url()).toBe('');
            });
        });
    }
);
