define(
    [
        'jquery', 'underscore',
        'js/utils/handle_iframe_binding'
    ],
function($, _, IframeBinding) {
    describe('IframeBinding', function() {
        var doc = document.implementation.createHTMLDocument('New Document');
        var iframe_html = '<iframe src="http://www.youtube.com/embed/NHd27UvY-lw" frameborder="0" height="350" width="618"></iframe>';
        iframe_html += '<iframe src="http://www.youtube.com/embed/NHd27UvY-lw?allowFullScreen=false" frameborder="0" height="350" width="618"></iframe>';
        iframe_html += '<embed type="application/x-shockwave-flash" src="http://www.youtube.com/embed/NHd27UvY-lw" height="315" width="560">';
        doc.body.innerHTML = iframe_html;

        var verify_no_modification = function(src) {
            iframe_html = '<iframe width="618" height="350" src="' + src + '" frameborder="0" allowfullscreen></iframe>';
            doc.body.innerHTML = iframe_html;

            IframeBinding.iframeBinding(doc);

            expect($(doc).find('iframe')[0].src).toEqual(src);
        };

        it('modifies src url of DOM iframe and embed elements when iframeBinding function is executed', function() {
            expect($(doc).find('iframe')[0].src).toEqual('http://www.youtube.com/embed/NHd27UvY-lw');
            expect($(doc).find('iframe')[1].src).toEqual('http://www.youtube.com/embed/NHd27UvY-lw?allowFullScreen=false');
            expect($(doc).find('embed')[0].hasAttribute('wmode')).toBe(false);

            IframeBinding.iframeBinding(doc);

            // after calling iframeBinding function: src url of iframes should have "wmode=transparent" in its querystring
            // and embed objects should have "wmode='transparent'" as an attribute
            expect($(doc).find('iframe')[0].src).toEqual('http://www.youtube.com/embed/NHd27UvY-lw?wmode=transparent');
            expect($(doc).find('iframe')[1].src).toEqual('http://www.youtube.com/embed/NHd27UvY-lw?wmode=transparent&allowFullScreen=false');
            expect($(doc).find('embed')[0].hasAttribute('wmode')).toBe(true);

            iframe_html = IframeBinding.iframeBindingHtml(iframe_html);

            // after calling iframeBinding function: src url of iframes should have "wmode=transparent" in its querystring
            // and embed objects should have "wmode='transparent'" as an attribute
            expect(iframe_html).toContain('<iframe src="http://www.youtube.com/embed/NHd27UvY-lw?wmode=transparent"');
            expect(iframe_html).toContainHtml(
              '<embed wmode="transparent" type="application/x-shockwave-flash"' +
              ' src="http://www.youtube.com/embed/NHd27UvY-lw"');
        });

        it('does not modify src url of DOM iframe if it is empty', function() {
            verify_no_modification('');
        });

        it('does nothing on tinymce iframe', function() {
            verify_no_modification('javascript:');
        });
    });
});
