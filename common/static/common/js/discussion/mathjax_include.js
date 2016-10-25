// See common/templates/mathjax_include.html for info on Fast Preview mode.
var disableFastPreview = true,
    vendorScript;
if (typeof MathJax === 'undefined') {
    if (disableFastPreview) {
        window.MathJax = {
            menuSettings: {CHTMLpreview: false}
        };
    }

    vendorScript = document.createElement('script');
    vendorScript.onload = function() {
        'use strict';
        var MathJax = window.MathJax,
            setMathJaxDisplayDivSettings;
        MathJax.Hub.Config({
            tex2jax: {
                inlineMath: [
                    ['\\(', '\\)'],
                    ['[mathjaxinline]', '[/mathjaxinline]']
                ],
                displayMath: [
                    ['\\[', '\\]'],
                    ['[mathjax]', '[/mathjax]']
                ]
            }
        });
        if (disableFastPreview) {
            MathJax.Hub.processSectionDelay = 0;
        }
        MathJax.Hub.signal.Interest(function(message) {
            if (message[0] === 'End Math') {
                setMathJaxDisplayDivSettings();
            }
        });
        setMathJaxDisplayDivSettings = function() {
            $('.MathJax_Display').each(function() {
                this.setAttribute('tabindex', '0');
                this.setAttribute('aria-live', 'off');
                this.removeAttribute('role');
                this.removeAttribute('aria-readonly');
            });
        };
    };
    vendorScript.src = 'https://cdn.mathjax.org/mathjax/2.6-latest/MathJax.js?config=TeX-MML-AM_SVG&delayStartupUntil=configured';
    document.body.appendChild(vendorScript);
}
