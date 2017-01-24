/**
Copyright (c) 2010-2012 Pathable

Permission is hereby granted, free of charge, to any person
obtaining a copy of this software and associated documentation
files (the "Software"), to deal in the Software without
restriction, including without limitation the rights to use,
copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following
conditions:

The above copyright notice and this permission notice shall be
included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.
https://github.com/pathable/truncate
**/
(function($) {

  // Matches trailing non-space characters.
  var chop = /(\s*\S+|\s)$/;

  // Return a truncated html string.  Delegates to $.fn.truncate.
  $.truncate = function(html, options) {
    return $('<div></div>').append(html).truncate(options).html();
  };

  // Truncate the contents of an element in place.
  $.fn.truncate = function(options) {
    if ($.isNumeric(options)) options = {length: options};
    var o = $.extend({}, $.truncate.defaults, options);

    return this.each(function() {
      var self = $(this);

      if (o.noBreaks) self.find('br').replaceWith(' ');

      var text = self.text();
      var excess = text.length - o.length;

      if (o.stripTags) self.text(text);

      // Chop off any partial words if appropriate.
      if (o.words && excess > 0) {
        excess = text.length - text.slice(0, o.length).replace(chop, '').length - 1;
      }

      if (excess < 0 || !excess && !o.truncated) return;

      // Iterate over each child node in reverse, removing excess text.
      $.each(self.contents().get().reverse(), function(i, el) {
        var $el = $(el);
        var text = $el.text();
        var length = text.length;

        // If the text is longer than the excess, remove the node and continue.
        if (length <= excess) {
          o.truncated = true;
          excess -= length;
          $el.remove();
          return;
        }

        // Remove the excess text and append the ellipsis.
        if (el.nodeType === 3) {
          $(el.splitText(length - excess - 1)).replaceWith(o.ellipsis);
          return false;
        }

        // Recursively truncate child nodes.
        $el.truncate($.extend(o, {length: length - excess}));
        return false;
      });
    });
  };

  $.truncate.defaults = {

    // Strip all html elements, leaving only plain text.
    stripTags: false,

    // Only truncate at word boundaries.
    words: false,

    // Replace instances of <br> with a single space.
    noBreaks: false,

    // The maximum length of the truncated html.
    length: Infinity,

    // The character to use as the ellipsis.  The word joiner (U+2060) can be
    // used to prevent a hanging ellipsis, but displays incorrectly in Chrome
    // on Windows 7.
    // http://code.google.com/p/chromium/issues/detail?id=68323
    ellipsis: '\u2026' // '\u2060\u2026'

  };

})(jQuery);
