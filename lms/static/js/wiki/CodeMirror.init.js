$(document).ready(function() {

  var editor = CodeMirror.fromTextArea(document.getElementById("id_content"), {
    mode: 'mitx_markdown',
    matchBrackets: true,
    theme: "default",
    lineWrapping: true,
  });
      
  //Store the inital contents so we can compare for unsaved changes
  var initial_contents = editor.getValue();
      
  window.onbeforeunload = function askConfirm() { //Warn the user before they navigate away
    if ( editor.getValue() != initial_contents ) {
      return "You have made changes to the article that have not been saved yet.";
    }
  };
  
  $(".btn-primary").click(function() {
    initial_contents = editor.getValue();
  });
  
});