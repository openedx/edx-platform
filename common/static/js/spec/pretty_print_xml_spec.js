describe('XML Formatting Lib', function() {
    'use strict';

    it('correctly format the xml', function() {
        var rawXml = '<breakfast><food><name>Belgian Waffles</name><price>$5.95</price></food></breakfast>',
            expectedXml = '<breakfast>\n  <food>\n    <name>Belgian Waffles</name>' +
                '\n    <price>$5.95</price>\n  </food>\n</breakfast>';

        expect(window.PrettyPrint.xml(rawXml)).toEqual(expectedXml);
    });

    it('correctly handles the whitespaces and newlines', function() {
        var rawXml = '<breakfast>     <food>  <name>Belgian Waffles</name>' +
                '\n\n\n<price>$5.95</price></food>   </breakfast>',
            expectedXml = '<breakfast>\n  <food>\n    <name>Belgian Waffles</name>' +
            '\n    <price>$5.95</price>\n  </food>\n</breakfast>';

        expect(window.PrettyPrint.xml(rawXml)).toEqual(expectedXml);
    });
});
