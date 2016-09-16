var vendorScript;
if (typeof MathJax === 'undefined') {
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
    vendorScript.src = 'https://cdn.mathjax.org/mathjax/2.6-latest/MathJax.js?config=TeX-MML-AM_SVG';
    document.body.appendChild(vendorScript);
}
