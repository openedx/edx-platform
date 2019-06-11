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
describe('utility.rewriteCdnLinksToStatic', function() {
    'use strict';
    it('does not replace "url" to "static url" if url is not following "cdn url" pattern', function() {
        expect(
            rewriteCdnLinksToStatic( // eslint-disable-line no-undef
            '<img src="/asset-v1:UCentralLah+Cs201+2019_1+type@asset+block/foo.x"/>')
        ).toBe('<img src="/asset-v1:UCentralLah+Cs201+2019_1+type@asset+block/foo.x"/>');
        expect(
            rewriteCdnLinksToStatic('<img src="/assets/foo.x"/>') // eslint-disable-line no-undef
        ).toBe('<img src="/assets/foo.x"/>');
    });
    it('does a replace of "cdn url" to "static url" if url is part of absolute url', function() {
        expect(
            rewriteCdnLinksToStatic( // eslint-disable-line no-undef
              '<img src="//prod-edxapp.edx-cdn.org/assets/foo.x"/>')
        ).toBe('<img src="/static/foo.x"/>');
        expect(
          rewriteCdnLinksToStatic( // eslint-disable-line no-undef
            '<img src="https://prod-edxapp.edx-cdn.org/assets/foo.x"/>')
        ).toBe('<img src="/static/foo.x"/>');
    });
});
