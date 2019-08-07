(function(define, undefined) {
    'use strict';
    define(['jquery', 'underscore', 'annotator_1.2.9'], function($, _, Annotator) {
    /**
     * Adds the Scroller Plugin which scrolls to a note with a certain id and
     * opens it.
     **/
        Annotator.Plugin.Scroller = function() {
        // Call the Annotator.Plugin constructor this sets up the element and
        // options properties.
            Annotator.Plugin.apply(this, arguments);
        };

        $.extend(Annotator.Plugin.Scroller.prototype, new Annotator.Plugin(), {
            getIdFromLocationHash: function() {
                return window.location.hash.substr(1);
            },

            pluginInit: function() {
                _.bindAll(this, 'onNotesLoaded');
            // If the page URL contains a hash, we could be coming from a click
            // on an anchor in the notes page. In that case, the hash is the id
            // of the note that has to be scrolled to and opened.
                if (this.getIdFromLocationHash()) {
                    this.annotator.subscribe('annotationsLoaded', this.onNotesLoaded);
                }
            },

            destroy: function() {
                this.annotator.unsubscribe('annotationsLoaded', this.onNotesLoaded);
            },

            onNotesLoaded: function(notes) {
                var hash = this.getIdFromLocationHash();
                this.annotator.logger.log('Scroller', {
                    'notes:': notes,
                    hash: hash
                });
                _.each(notes, function(note) {
                    var $highlight, offset;
                    if (note.id === hash && note.highlights.length) {
                    // Clear the page URL hash, it won't be needed once we've
                    // scrolled and opened the relevant note. And it would
                    // unnecessarily repeat the steps below if we come from
                    // another sequential.
                        window.location.hash = '';
                        $highlight = $(note.highlights[0]);
                        offset = $highlight.position();
                    // Open the note
                        this.annotator.showFrozenViewer([note], {
                            top: offset.top + 0.5 * $highlight.height(),
                            left: offset.left + 0.5 * $highlight.width()
                        });
                    // Freeze the viewer
                        this.annotator.freezeAll();
                    // Scroll to highlight
                        this.scrollIntoView($highlight);
                    }
                }, this);
            },

            scrollIntoView: function(highlight) {
                highlight.focus();
            }
        });
    });
}).call(this, define || RequireJS.define);
