describe('utility.rewriteStaticLinks', function () {
    it('returns "content" if "from" or "to" is null', function () {
        expect(rewriteStaticLinks('foo', null, 'bar')).toBe('foo');
        expect(rewriteStaticLinks('foo', 'bar', null)).toBe('foo');
        expect(rewriteStaticLinks('foo', null, null)).toBe('foo');
    });
    it('does a replace of "from" to "to"', function () {
        expect(rewriteStaticLinks('<img src="/static/foo.x"/>', '/static/', 'howdy')).toBe('<img src="howdyfoo.x"/>')
    });
    it('returns "content" if "from" is not found', function () {
        expect(rewriteStaticLinks('<img src="/static/foo.x"/>', '/statix/', 'howdy')).toBe('<img src="/static/foo.x"/>')
    });
    it('does not replace of "from" to "to" if "from" is part of absolute url', function () {
        expect(
            rewriteStaticLinks('<img src="http://www.mysite.org/static/foo.x"/>', '/static/', 'howdy')
        ).toBe('<img src="http://www.mysite.org/static/foo.x"/>')
    });
});

describe('utility.appendParameter', function() {
    it('creates and populates query string with provided parameter', function() {
        expect(appendParameter('/cambridge', 'season', 'fall')).toBe('/cambridge?season=fall')
    });
    it('appends provided parameter to existing query string parameters', function() {
        expect(appendParameter('/cambridge?season=fall', 'color', 'red')).toBe('/cambridge?season=fall&color=red')
    });
    it('appends provided parameter to existing query string with a trailing ampersand', function() {
        expect(appendParameter('/cambridge?season=fall&', 'color', 'red')).toBe('/cambridge?season=fall&color=red')
    });
    it('overwrites existing parameter with provided value', function() {
        expect(appendParameter('/cambridge?season=fall', 'season', 'winter')).toBe('/cambridge?season=winter');
        expect(appendParameter('/cambridge?season=fall&color=red', 'color', 'orange')).toBe('/cambridge?season=fall&color=orange');
    });
});

describe('utility.parseQueryString', function() {
    it('converts a non-empty query string into a key/value object', function() {
        expect(JSON.stringify(parseQueryString('season=fall'))).toBe(JSON.stringify({season:'fall'}));
        expect(JSON.stringify(parseQueryString('season=fall&color=red'))).toBe(JSON.stringify({season:'fall', color:'red'}));
    });
});
