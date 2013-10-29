/* By default, CodeMirror turns tabs into indents, which makes it difficult for keyboard-only
   users to "tab through" elements on a page.  Including this file and setting keyMap to 
   "accessible" removes the "tab" from CodeMirror's default KeyMap to remedy this problem */

(function() {
  var keyMap = CodeMirror.keyMap.accessible = {
  	"Left": "goCharLeft", 
  	"Right": "goCharRight", 
  	"Up": "goLineUp", 
  	"Down": "goLineDown",
    "End": "goLineEnd", 
    "Home": "goLineStartSmart", 
    "PageUp": "goPageUp", 
    "PageDown": "goPageDown",
    "Delete": "delCharAfter", 
    "Backspace": "delCharBefore", 
    "Shift-Backspace": "delCharBefore",
    "Alt-Tab": "insertTab",
    "Alt-Shift-Tab": "insertTab",
    "Tab": false,
    "Shift-Tab": false, 
    "Enter": "newlineAndIndent", 
    "Insert": "toggleOverwrite", 
    fallthrough: "default"
  };
})();