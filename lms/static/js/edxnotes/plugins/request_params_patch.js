(function(define, undefined) {
    'use strict';

    define(['jquery', 'underscore', 'annotator_1.2.9'], function($, _, Annotator) {
    /**
     * Overrides Annotator.Plugin.Store.prototype._apiRequestOptions to modify query params
     */
        var originalApiRequestOptions = Annotator.Plugin.Store.prototype._apiRequestOptions;
        Annotator.Plugin.Store.prototype._apiRequestOptions = function(action, obj, onSuccess) {
            if (action != "search") {
                _.extend(
                    obj, 
                    {
                        'usage_id': $(this.annotator.selectedRanges[0].commonAncestor)
                        .closest('.edx-notes-wrapper')
                        .data('usageId')
                    }
                )
            }
            return originalApiRequestOptions.call(this, action, obj, onSuccess);
        };
    });
}).call(this, define || RequireJS.define);

