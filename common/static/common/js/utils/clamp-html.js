/**
 * Used to ellipsize a section of arbitrary HTML after a specified number of words.
 *
 * Note: this will modify the DOM structure of root in place.
 * To keep the original around, you may want to save the result of cloneNode(true) before calling this method.
 *
 * Known bug: This method will ignore any special whitespace in the source and simply output single spaces.
 * Which means that &nbsp; will not be respected. This is not considered worth solving at time of writing.
 *
 * Returns how many words remain (or a negative number if the content got clamped)
 */
function clampHtmlByWords(root, wordsLeft) {
    'use strict';

    if (root.nodeName === 'SCRIPT' || root.nodeName === 'STYLE') {
        return wordsLeft; // early exit and ignore
    }

    var remaining = wordsLeft;
    var nodes = Array.from(root.childNodes ? root.childNodes : []);
    var words, chopped;

    // First, cut short any text in our node, as necessary
    if (root.nodeName === '#text' && root.data) {
        // split on words, ignoring any resulting empty strings
        words = root.data.split(/\s+/).filter(Boolean);
        if (remaining < 0) {
            root.data = ''; // eslint-disable-line no-param-reassign
        } else if (remaining > words.length) {
            remaining -= words.length;
        } else {
            // OK, let's add an ellipsis and cut some of root.data
            chopped = words.slice(0, remaining).join(' ') + '…';
            // But be careful to get any preceding space too
            if (root.data.match(/^\s/)) {
                chopped = ' ' + chopped;
            }
            root.data = chopped; // eslint-disable-line no-param-reassign
            remaining = -1;
        }
    }

    // Now do the same for any child nodes
    nodes.forEach(function(node) {
        if (remaining < 0) {
            root.removeChild(node);
        } else {
            remaining = clampHtmlByWords(node, remaining);
        }
    });

    return remaining;
}

module.exports = {
    clampHtmlByWords: clampHtmlByWords
};
