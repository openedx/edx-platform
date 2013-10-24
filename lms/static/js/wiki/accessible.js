/* By default, CodeMirror turns tabs into indents, which makes it difficult for keyboard-only
   users to "tab through" elements on a page.  Including this file and setting keyMap to 
   "accessible" removes the "tab" from CodeMirror's default KeyMap to remedy this problem */

var keyMap = CodeMirror.keyMap.accessible = {
  "Left": "goCharLeft", "Right": "goCharRight", "Up": "goLineUp", "Down": "goLineDown",
  "End": "goLineEnd", "Home": "goLineStartSmart", "PageUp": "goPageUp", "PageDown": "goPageDown",
  "Delete": "delCharRight", "Backspace": "delCharLeft", "Shift-Tab": "indentAuto",
  "Enter": "newlineAndIndent", "Insert": "toggleOverwrite"
};
