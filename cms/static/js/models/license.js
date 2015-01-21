define(["backbone", "backbone.associations"], function(Backbone) {
    /**
     * License model used to store the license kind and version
     * for course and video assets.
     *
     * In terms of the kind of licenses, the following options are
     * used:
     * ARR      - All rights reserved
     * CC0      - Creative Commons Zero license (no rights reserved)
     * CC-BY-*  - Creative Commons Attribution license
     * CC-*-ND  - Creative Commons NoDerivatives license
     * CC-*-NC  - Creative Commons NonCommercial license
     * CC-*-SA  - Creative Commons ShareAlike license
     */
    var License = Backbone.AssociatedModel.extend({
        defaults: {
            kind: "ARR",
            version: ""
        },

        validate: function(newattrs) {
            var errors = {};
            if (newattrs.kind instanceof String) {
                var kind, validKind;
                kind = newattrs.kind;

                if (kind === "ARR" || kind === "CC0") {
                    validKind = kind;
                }
                else {
                    var attr = kind.split("-");

                    if (attr.length > 1 && attr[0] === "CC" && attr[1] === "BY") {
                        validKind = attr.join("-");
                    }
                    else {
                        validKind = "NONE";
                    }
                }

                newattrs.kind = validKind;
            }
            else {
                newattrs.kind = "NONE";
            }
            if (!_.isEmpty(errors)) return errors;
            // NOTE don't return empty errors as that will be interpreted as an error state
        },
    });
    return License;
});
