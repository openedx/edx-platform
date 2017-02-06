describe('utility.rewriteStaticLinks', function() {
    it('returns "content" if "from" or "to" is null', function() {
        expect(rewriteStaticLinks('foo', null, 'bar')).toBe('foo');
        expect(rewriteStaticLinks('foo', 'bar', null)).toBe('foo');
        expect(rewriteStaticLinks('foo', null, null)).toBe('foo');
    });
    it('does a replace of "from" to "to"', function() {
        expect(rewriteStaticLinks('<img src="/static/foo.x"/>', '/static/', 'howdy')).toBe('<img src="howdyfoo.x"/>');
    });
    it('returns "content" if "from" is not found', function() {
        expect(rewriteStaticLinks('<img src="/static/foo.x"/>', '/statix/', 'howdy')).toBe('<img src="/static/foo.x"/>');
    });
    it('does not replace of "from" to "to" if "from" is part of absolute url', function() {
        expect(
            rewriteStaticLinks('<img src="http://www.mysite.org/static/foo.x"/>', '/static/', 'howdy')
        ).toBe('<img src="http://www.mysite.org/static/foo.x"/>');
    });
});
