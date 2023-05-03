(function() {
    'use strict';
    this.JavascriptLoader = (function() {
        function JavascriptLoader() {
        }

        /**
         * Set of library functions that provide common interface for javascript loading
         * for all module types. All functionality provided by JavascriptLoader should take
         * place at module scope, i.e. don't run jQuery over entire page.
         *
         * executeModuleScripts:
         *     Scan the module ('el') for "script_placeholder"s, then:
         *
         *     1) Fetch each script from server
         *     2) Explicitly attach the script to the <head> of document
         *     3) Explicitly wait for each script to be loaded
         *     4) Return to callback function when all scripts loaded
         */
        JavascriptLoader.executeModuleScripts = function(el, callback) {
            var callbackCalled, completed, completionHandlerGenerator, loaded, placeholders;
            if (!callback) {
                callback = null; // eslint-disable-line no-param-reassign
            }
            placeholders = el.find('.script_placeholder');
            if (placeholders.length === 0) {
                if (callback !== null) {
                    callback();
                }
                return [];
            }
            // TODO: Verify the execution order of multiple placeholders
            completed = (function() {
                var i, ref, results;
                results = [];
                for (i = 1, ref = placeholders.length; ref >= 1 ? i <= ref : i >= ref; ref >= 1 ? ++i : --i) {
                    results.push(false);
                }
                return results;
            }());
            callbackCalled = false;
            completionHandlerGenerator = function(index) {
                return function() {
                    var allComplete, flag, i, len;
                    allComplete = true;
                    completed[index] = true;
                    for (i = 0, len = completed.length; i < len; i++) {
                        flag = completed[i];
                        if (!flag) {
                            allComplete = false;
                            break;
                        }
                    }
                    if (allComplete && !callbackCalled) {
                        callbackCalled = true;
                        if (callback !== null) {
                            return callback();
                        }
                    }
                    return undefined;
                };
            };
            // Keep a map of what sources we're loaded from, and don't do it twice.
            loaded = {};
            return placeholders.each(function(index, placeholder) {
                var s, src;
                // TODO: Check if the script already exists in DOM. If so, (1) copy it
                // into memory; (2) delete the DOM script element; (3) reappend it.
                // This would prevent memory bloat and save a network request.
                src = $(placeholder).attr('data-src');
                if (!(src in loaded)) {
                    loaded[src] = true;
                    s = document.createElement('script');
                    s.setAttribute('src', src);
                    s.setAttribute('type', 'text/javascript');
                    s.onload = completionHandlerGenerator(index);
                    // Need to use the DOM elements directly or the scripts won't execute properly.
                    $('head')[0].appendChild(s);
                } else {
                    // just call the completion callback directly, without reloading the file
                    completionHandlerGenerator(index)();
                }
                return $(placeholder).remove();
            });
        };

        return JavascriptLoader;
    }());
}).call(this);
