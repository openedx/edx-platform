(function(define) {
    'use strict';

    define(['annotator_1.2.9'], function(Annotator) {
        //
        // Override Annotator.Plugin.Store.prototype._getAnnotations. We don't want AnnotatorJS to search notes.
        //
        // eslint-disable-next-line no-param-reassign, no-underscore-dangle
        Annotator.Plugin.Store.prototype._getAnnotations = function() {
            // Do Nothing
        };
    });
}).call(this, define || RequireJS.define);
