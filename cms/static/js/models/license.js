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
     *
     * For the CC license, a combination of these flags is allowed.
     * Support is limited to ARR, CC0, and CC v4.0 licenses.
     */
    var License = Backbone.AssociatedModel.extend({
        defaults: {
            kind: "ARR",
            version: ""
        },

        toggleAttribute: function(attr) {
          var attrNC, attrND, attrSA, newKind, newVersion;

          if (attr === 'ARR') {
            newKind = 'ARR';
            newVersion = '';
          } else {
            // Determine which attributes are set
            attrNC = /NC/.test(this.get('kind'));
            attrND = /ND/.test(this.get('kind'));
            attrSA = /SA/.test(this.get('kind'));

            // Toggle the attribute accordingly
            if (attr === 'NC') {
              attrNC = !attrNC;
            } else if (attr === 'ND') {
              attrND = !attrND;
              if (attrND) {
                // The SA and ND attributes cannot be set at the same time
                attrSA = false;
              }
            } else if (attr === 'SA') {
              attrSA = !attrSA;
              if (attrSA) {
                // The SA and ND attributes cannot be set at the same time
                attrND = false;
              }
            }

            // Construct the new kind value
            newKind = 'CC-BY';
            if (attrNC) {
              newKind += '-NC';
            }
            if (attrND) {
              newKind += '-ND';
            }
            if (attrSA) {
              newKind += '-SA';
            }
            newVersion = '4.0';
          }

          // Save the new kind
          this.set({kind: newKind, version: newVersion});
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
                        validKind = null;
                    }
                }

                newattrs.kind = validKind;
            }
            else {
                newattrs.kind = null;
            }
            if (!_.isEmpty(errors)) {
                // NOTE don't return empty errors as that will be interpreted as an error state
                return errors;
            }
        },
    });
    return License;
});
