// eslint-disable-next-line no-undef
define(['jquery'], function($) {
    var iframeBinding = function(e) {
        // eslint-disable-next-line camelcase
        var target_element = null;
        if (typeof e === 'undefined') {
            // eslint-disable-next-line camelcase
            target_element = $('iframe, embed');
        } else {
            if (typeof e.nodeName !== 'undefined') {
                // eslint-disable-next-line camelcase
                target_element = $(e).find('iframe, embed');
            } else {
                // eslint-disable-next-line camelcase
                target_element = e.$('iframe, embed');
            }
        }
        // eslint-disable-next-line no-use-before-define
        modifyTagContent(target_element);
    };

    // eslint-disable-next-line camelcase
    var modifyTagContent = function(target_element) {
        // eslint-disable-next-line camelcase
        target_element.each(function() {
            if ($(this).prop('tagName') === 'IFRAME') {
                // eslint-disable-next-line camelcase
                var ifr_source = $(this).attr('src');

                // Modify iframe src only if it is not empty
                // eslint-disable-next-line camelcase
                if (ifr_source) {
                    var wmode = 'wmode=transparent';
                    // eslint-disable-next-line camelcase
                    if (ifr_source.indexOf('?') !== -1) {
                        // eslint-disable-next-line camelcase
                        var getQString = ifr_source.split('?');
                        if (getQString[1].search('wmode=transparent') === -1) {
                            var oldString = getQString[1];
                            var newString = getQString[0];
                            $(this).attr('src', newString + '?' + wmode + '&' + oldString);
                        }
                    // eslint-disable-next-line brace-style
                    }
                    // The TinyMCE editor is hosted in an iframe, and before the iframe is
                    // removed we execute this code. To avoid throwing an error when setting the
                    // attr, check that the source doesn't start with the value specified by TinyMCE ('javascript:""').
                    /* eslint-disable-next-line no-script-url, camelcase */
                    else if (ifr_source.lastIndexOf('javascript:', 0) !== 0) {
                        // eslint-disable-next-line camelcase
                        $(this).attr('src', ifr_source + '?' + wmode);
                    }
                }
            } else {
                $(this).attr('wmode', 'transparent');
            }
        });
    };

    // Modify iframe/embed tags in provided html string
    // Use this method when provided data is just html sting not dom element
    // This method will only modify iframe (add wmode=transparent in url querystring) and embed (add wmode=transparent as attribute)
    // tags in html string so both tags will attach to dom and don't create z-index problem for other popups
    // Note: embed tags should be modified before rendering as they are static objects as compared to iframes
    // Note: this method can modify unintended html (invalid tags) while converting to dom object
    // eslint-disable-next-line camelcase
    var iframeBindingHtml = function(html_string) {
        // eslint-disable-next-line camelcase
        if (html_string) {
            // eslint-disable-next-line camelcase
            var target_element = null;
            // eslint-disable-next-line camelcase
            var temp_content = document.createElement('div');
            $(temp_content).html(html_string);
            // eslint-disable-next-line camelcase
            target_element = $(temp_content).find('iframe, embed');
            // eslint-disable-next-line camelcase
            if (target_element.length > 0) {
                modifyTagContent(target_element);
                // eslint-disable-next-line camelcase
                html_string = $(temp_content).html();
            }
        }
        // eslint-disable-next-line camelcase
        return html_string;
    };

    return {
        iframeBinding: iframeBinding,
        iframeBindingHtml: iframeBindingHtml
    };
});
