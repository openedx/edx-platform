// This file is designed to load all the XModule Javascript files in one wad
// using requirejs. It is passed through the Mako template system, which
// populates the `urls` variable with a list of paths to XModule JS files.
// These files assume that several libraries are available and bound to
// variables in the global context, so we load those libraries with requirejs
// and attach them to the global context manually.
define(
    [
        'jquery', 'underscore', 'codemirror', 'tinymce', 'scriptjs',
        'jquery.tinymce', 'jquery.qtip', 'jquery.scrollTo', 'jquery.flot',
        'jquery.cookie',
        'utility'
    ],
    function($, _, CodeMirror, tinymce, $script) {
        'use strict';

        window.$ = $;
        window._ = _;

        $script(
            'https://cdn.jsdelivr.net/npm/mathjax@2.7.5/MathJax.js' +
            '?config=TeX-MML-AM_HTMLorMML&delayStartupUntil=configured',
            'mathjax',
            function() {
                window.MathJax.Hub.Config({
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

                // In order to eliminate all flashing during interactive
                // preview, it is necessary to set processSectionDelay to 0
                // (remove delay between input and output phases). This
                // effectively disables fast preview, regardless of
                // the fast preview setting as shown in the context menu.
                window.MathJax.Hub.processSectionDelay = 0;
                window.MathJax.Hub.Configured();
            }
        );
        window.CodeMirror = CodeMirror;
        window.RequireJS = {
            requirejs: {}, // This is never used by current xmodules
            require: $script, // $script([deps], callback) acts approximately like the require function
            define: define
        };
        /**
         * Loads all modules one-by-one in exact order.
         * The module should be used until we'll use RequireJS for XModules.
         * @param {Array} modules A list of urls.
         * @return {jQuery Promise}
         **/
        function requireQueue(modules) {
            var deferred = $.Deferred();
            function loadScript(queue) {
                $script.ready('mathjax', function() {
                    // Loads the next script if queue is not empty.
                    if (queue.length) {
                        $script([queue.shift()], function() {
                            loadScript(queue);
                        });
                    } else {
                        deferred.resolve();
                    }
                });
            }

            loadScript(modules.concat());
            return deferred.promise();
        }

        // if (!window.xmoduleUrls) {
        //     throw Error('window.xmoduleUrls must be defined');
        // }
        return requireQueue([]);
    }
);
