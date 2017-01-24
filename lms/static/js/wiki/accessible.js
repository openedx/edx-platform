/* By default, CodeMirror turns tabs into indents, which makes it difficult for keyboard-only
   users to "tab through" elements on a page.  Including this file and setting keyMap to
   "accessible" removes the "tab" from CodeMirror's default KeyMap to remedy this problem */

(function() {
    var keyMap = CodeMirror.keyMap.accessible = {
        'Tab': false,
        'Shift-Tab': false,
        fallthrough: 'default'
    };
})();
