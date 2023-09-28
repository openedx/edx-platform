$(document).ready(function() {
    var editor = CodeMirror.fromTextArea(document.getElementById('id_content'), {
        mode: 'edx_markdown',
        matchBrackets: true,
        theme: 'default',
        lineWrapping: true,
        keyMap: 'accessible'
    });

    // Store the inital contents so we can compare for unsaved changes
    var initialContents = editor.getValue();

    // The Wiki associates a label with the text area that has ID "id_content". However, when we swap in
    // CodeMirror, that text area is hidden. We need to associate the label with visible CodeMirror text area
    // (and there is JS code in the wiki that depends on "id_content" interact with the content, so we have
    // to leave that alone).
    editor.getInputField().setAttribute('id', 'id_codemirror_content');
    $(".control-label[for='id_content']")[0].setAttribute('for', 'id_codemirror_content');
    window.onbeforeunload = function askConfirm() { // Warn the user before they navigate away
        if (editor.getValue() != initialContents) {
            return 'You have made changes to the article that have not been saved yet.';
        }
    };

    $('.btn-primary').click(function() {
        initialContents = editor.getValue();
    });
});
