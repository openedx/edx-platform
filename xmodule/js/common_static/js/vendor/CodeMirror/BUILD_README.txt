Instructions for creating codemirror-compressed.js (in top-level vendor directory).

1. Install uglifyjs and put it on your path.
2. In the CodeMirror directory, run "cat codemirror.js addons/* addons/dialog/dialog.js | uglifyjs > codemirror-compressed.js"
3. Replace existing codemirror-compressed.js file with the generated one.

Additions to codemirror.css are done by manually copying in the new content.
