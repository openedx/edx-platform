var vendorScript;
if (typeof MathJax === 'undefined') {
    vendorScript = document.createElement('script');
    vendorScript.onload = function() {
        'use strict';

        window.MathJax = {
            tex: {
                inlineMath: [
                    ['\\(', '\\)'],
                    ['[mathjaxinline]', '[/mathjaxinline]']
                ],
                displayMath: [
                    ['\\[', '\\]'],
                    ['[mathjax]', '[/mathjax]']
                ],
                autoload: {
                    color: [],
                    colorv2: ['color']
                },
                packages: {'[+]': ['noerrors']}
            },
            options: {
                ignoreHtmlClass: 'tex2jax_ignore',
                processHtmlClass: 'tex2jax_process',
                menuOptions: {
                    settings: {
                        collapsible: true,
                        explorer: true
                    },
                },
            },
            loader: {
                load: ['input/asciimath', '[tex]/noerrors']
            }
        };
    };
    vendorScript.src = 'https://cdn.jsdelivr.net/npm/mathjax@3.2.1/es5/tex-mml-svg.js';
    document.body.appendChild(vendorScript);
}
