if (typeof edx === 'undefined') {
    var vendorScript,
        vendorScriptURLs = [
            '/static/edx-ui-toolkit/js/utils/string-utils.js',
            '/static/edx-ui-toolkit/js/utils/html-utils.js'
        ];
    vendorScript = document.createElement("script");
    vendorScript.onload = function() {
        'use strict';
        vendorScriptURLs.forEach(function(vendorScriptURL) {
            vendorScript = document.createElement("script");
            vendorScript.src = vendorScriptURL;
            document.head.appendChild(vendorScript);
        });
    };
    vendorScript.src = '/static/edx-ui-toolkit/js/utils/global-loader.js';
    document.head.appendChild(vendorScript);
}
