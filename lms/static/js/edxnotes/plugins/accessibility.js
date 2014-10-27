(function (define, $, _, Annotator, undefined) {
    'use strict';
    define('edxnotes/plugins/accessibility', function () {
        var wrap = function (orig, wrapper) {
            Annotator.prototype[orig] = _.wrap(Annotator.prototype[orig], function (func) {
                var args = Array.prototype.slice.call(arguments, 1);
                wrapper.apply(this, args);
                return func.apply(this, args);
            });
        };

        /**
         * Sets up the selection event listeners to watch keyboard actions on the document.
         * @return {this} Returns itself for chaining.
         **/
        wrap('_setupDocumentEvents', function () {
            $(document).on({
                'keyup':     _.bind(this.checkForKeyboardEndSelection, this),
                'keydown':   _.bind(this.checkForKeyboardStartSelection, this),
                'mousedown': _.bind(this.cleanupPosition, this)
            });
        });

        /**
         * Annotator#element callback. Sets the @keyIsDown property used to
         * determine if a selection may have started to true. Also calls
         * Annotator#startViewerHideTimer() to hide the Annotator#viewer.
         * @param {jQuery Event} event A keydown Event object.
         **/
        Annotator.prototype.checkForKeyboardStartSelection = function (event) {
            if (event && this.isAnnotator(event.target)) {
                this.startViewerHideTimer();
            }
            this.keyIsDown = true;
        };

        Annotator.prototype.cleanupPosition = function () {
            this.adder.css({
                        'position': 'absolute',
                        'left': null,
                        'top': null
                    })
                    .removeClass('is-fixed');
        };

        Annotator.prototype.checkForKeyboardEndSelection = _.debounce(function (event) {
            this.keyIsDown = false;

            // This prevents the note image from jumping away on the keyup
            // of a click on icon.
            if (this.ignoreKeyup) {
                return false;
            }

            // Get the currently selected ranges.
            this.selectedRanges = this.getSelectedRanges();
            for (var i = 0, len = this.selectedRanges.length; i < len; i++) {
                var range = this.selectedRanges[i],
                    container = range.commonAncestor;

                if ($(container).hasClass('annotator-hl')) {
                    container = $(container).parents('[class!=annotator-hl]')[0];
                }
                if (this.isAnnotator(container)) {
                    return false;
                }
            }

            if (this.selectedRanges.length) {
                this.adder
                    // Show icon at the right left side of the window.
                    .css({
                        'position': 'fixed',
                        'left': 30,
                        'top': 60
                    })
                    .addClass('is-fixed')
                    .show();
            } else {
                this.adder.hide();
                this.cleanupPosition();
            }
        }, 300);
    });
}).call(this, RequireJS.define, jQuery, _, Annotator);
