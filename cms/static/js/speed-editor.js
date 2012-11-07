var $body;
var $preview;
var $tooltip;
var simpleEditor;
var xmlEditor;
var currentEditor;
var controlDown;
var commandDown;


function initProblemEditors($editor, $prev) {
  simpleEditor = CodeMirror.fromTextArea($editor.find('.edit-box')[0], {
    lineWrapping: true,
    extraKeys: {
      'Ctrl-N': newUnit,
      'Ctrl-H': makeHeader,          
      'Ctrl-V': makeVideo,
      'Ctrl-M': makeMultipleChoice,
      'Ctrl-C': makeCheckboxes,
      'Ctrl-S': makeStringInput,
      'Shift-Ctrl-3': makeNumberInput,
      'Shift-Ctrl-S': makeSelect
    },
    mode: null,
    onChange: onSimpleEditorUpdate
  });

  xmlEditor = CodeMirror.fromTextArea($editor.find('.xml-box')[0], {
    lineWrapping: true,
    mode: 'xml',
    lineNumbers: true
  });

  currentEditor = simpleEditor;

  $(simpleEditor.getWrapperElement()).css('background', '#fff');
  $(xmlEditor.getWrapperElement()).css({
    'background': '#fff'
  }).hide();

  $(simpleEditor.getWrapperElement()).bind('click', setFocus);
  $preview = $prev.find('.problem');

  $body.on('click', '.editor-bar a', onEditorButton);
  $body.on('click', '.editor-tabs a', setEditorTab);
  $(document).bind('keyup', onKeyboard);
}

function setEditorTab(e) {
  e.preventDefault();
  $('.editor-tabs .current').removeClass('current');
  $(this).addClass('current');
  if($(this).hasClass('simple-tab')) {
    currentEditor = simpleEditor;
    $(simpleEditor.getWrapperElement()).show();          
    $(xmlEditor.getWrapperElement()).hide();
    $(simpleEditor).focus();
  } else {
    currentEditor = xmlEditor;
    $(simpleEditor.getWrapperElement()).hide();
    $(xmlEditor.getWrapperElement()).show();
    $(xmlEditor).focus();
  }
  onSimpleEditorUpdate();
}

function setFocus(e) {
  $(simpleEditor).focus();
}

function onSimpleEditorUpdate() {
  updatePreview();
  updateXML();
}

function updateXML() {
  var val = simpleEditor.getValue();
  var xml = val;

  // replace headers
  xml = xml.replace(/(^.*)\n(?=\=\=+)/g, '<h1>$1</h1>');
  xml = xml.replace(/\=\=+/g, '');

  // group multiple choice answers
  xml = xml.replace(/(\(.?\).*\n*)+/g, function(match, p) {
    var groupString = '<multiplechoiceresponse>\n';
    groupString += '  <choicegroup type="MultipleChoice">\n';
    var options = match.split('\n');
    for(var i = 0; i < options.length; i++) {
      if(options[i].length > 0) {
        var value = options[i].split(/\)\s*/)[1];
        var correct = /\(x\)/i.test(options[i]);
        groupString += '    <choice correct="' + correct + '">' + value + '</choice>\n';
      }
    }          
    groupString += '  </choicegroup>\n';
    groupString += '</multiplechoiceresponse>\n\n';
    return groupString;
  });

  // group check answers
  xml = xml.replace(/(\[.?\].*\n*)+/g, function(match, p) {
    var groupString = '<multiplechoiceresponse>\n';
    groupString += '  <choicegroup type="MultipleChoiceChecks">\n';
    var options = match.split('\n');
    for(var i = 0; i < options.length; i++) {
      if(options[i].length > 0) {
        var value = options[i].split(/\]\s*/)[1];
        var correct = /\[x\]/i.test(options[i]);
        groupString += '    <choice correct="' + correct + '">' + value + '</choice>\n';
      }
    }          
    groupString += '  </choicegroup>\n';
    groupString += '</multiplechoiceresponse>\n\n';
    return groupString;
  });

  // replace videos
  xml = xml.replace(/\{\{video\s(.*)\}\}/g, '<video youtube="1.0:$1" />\n\n');

  // replace string input
  xml = xml.replace(/\_\_\_\[(.+)\]/g, '<stringresponse answer="$1" type="ci">\n  <textline size="20"/>\n</stringresponse>\n\n');

  // replace numerical input
  xml = xml.replace(/\#\#\#\[(.+)\]/g, function(match, p) {
    var solution = extractNumericalSolution(p);
    var string = '<numericalresponse answer="' + solution + '">\n';

    var params = extractNumericalSettings(p);

    if(params) {
      for(var i = 0; i < params.length; i++) {
        var splitProp = params[i].split(/:\s*/);
        string += '  <responseparam type="' + splitProp[0] + '" default="' + splitProp[1] + '" />\n';
      }
    }
                        
    string += '  <textline />\n';
    string += '</numericalresponse>\n\n';
    return string;
  });

  // replace selects
  xml = xml.replace(/\[\[(.+)\]\]/g, function(match, p) {
    var selectString = '\n<optionresponse>\n';
    selectString += '  <optioninput options="(';
    var options = p.split(/\,\s*/g);
    for(var i = 0; i < options.length; i++) {            
      selectString += "'" + options[i].replace(/\((.*)\)/g, '$1') + "'" + (i < options.length -1 ? ',' : '');
    }
    selectString += ')" correct="';
    selectString += p.split(/\(/)[1].split(/\)/)[0];
    selectString += '"></optioninput>\n';
    selectString += '</optionresponse>\n\n';
    return selectString;
  });

  // split scripts and wrap paragraphs
  var splits = xml.split(/(\<\/?script.*\>)/g);
  var scriptFlag = false;
  for(var i = 0; i < splits.length; i++) {
    if(/\<script/.test(splits[i])) {
      scriptFlag = true; 
    }
    if(!scriptFlag) {
      splits[i] = splits[i].replace(/(^(?!\s*\<|$).*$)/gm, '<p>$1</p>');
    }          
    if(/\<\/script/.test(splits[i])) {
      scriptFlag = false;
    }
  }
  xml = splits.join('');

  // rid white space
  xml = xml.replace(/\n\n\n/g, '\n');

  // console.log(xml);

  xmlEditor.setValue(xml);
}

function updatePreview() {
  var val = simpleEditor.getValue();
  var html = val;

  // replace headers
  html = html.replace(/(^.*)\n(?=\=\=+)/g, '<h1>$1</h1>');
  html = html.replace(/\=\=+/g, '');

  // group multiple choice answers
  html = html.replace(/(\(.?\).*\n*)+/g, function(match, p) {
    var groupString = '<form class="choicegroup">\n';
    groupString += '  <div class="indicator_container"><span class="unanswered" id=""></span></div>';
    groupString += '  <fieldset>\n';
    
    var options = match.split('\n');
    for(var i = 0; i < options.length; i++) {
      if(options[i].length > 0) {
        // groupString += '  <li>' + options[i] + '</li>\n';
        groupString += '    <label>' + options[i] + '</label>\n';
      }
    }
    groupString += '  </fieldset>\n';
    groupString += '</form>\n';
    return groupString;
  });

  // group check answers
  html = html.replace(/(\[.?\].*\n*)+/g, function(match, p) {
    var groupString = '<ul class="check-choice-group">\n';
    var options = match.split('\n');
    for(var i = 0; i < options.length; i++) {
      if(options[i].length > 0) {
        groupString += '  <li>' + options[i] + '</li>\n';  
      }
    }          
    groupString += '</ul>\n';
    return groupString;
  });

  // wrap the paragraphs
  html = html.replace(/(^(?!\<\/*ul|\s*\<li|\<h1|\s*\<label|\s*$).*$)/gm, '<p>$1</p>\n');

  // replace videos
  html = html.replace(/\{\{video\s(.*)\}\}/g, function(match, p) {
    var id = p.replace(/.*1\.0\:/g, '').replace(/\,.*/g, '');
    var string = '<iframe width="420" height="315" src="http://www.youtube.com/embed/' + id + '" frameborder="0" allowfullscreen></iframe>';
    return string;
  });

  // replace checkboxes
  html = html.replace(/\[\s*\]/g, '<input type="checkbox">');
  html = html.replace(/\[x\]/gi, '<input type="checkbox" checked>');

  // replace radios
  html = html.replace(/\(\s*\)/g, '<input type="radio" name="multiple-choice-id">');
  html = html.replace(/\(x\)/gi, '<input type="radio" checked name="multiple-choice-id">');

  // replace string input
  html = html.replace(/\_\_\_\[(.+)\]/g, function(match, p) {
    var string = '<input type="text" name="" id="" value="' + p + '" size="20">\n';
    return string;
  });

  // replace numerical input
  html = html.replace(/\#\#\#\[(.+)\]/g, '<input type="text"><small>$1</small>');

  // replace selects
  html = html.replace(/\[\[(.+)\]\]/g, function(match, p) {
    var selectString = '<select>\n';
    selectString += '  <option disabled selected></option>\n';
    var options = p.split(/\,\s*/g);
    for(var i = 0; i < options.length; i++) {
      var isAnswer = /\(.*\)/.test(options[i]);
      selectString += '  <option data-answer="' + (isAnswer ? 'true' : 'false') + '"">' + options[i].replace(/\((.*)\)/g, '$1') + '</option>\n'; 
    }
    selectString += '</select>\n';
    return selectString;
  });

  html = html.replace(/\n\n/g, '');

  // console.log(html);

  $preview.html(html);
}

function extractNumericalSolution(string) {
  var solution = string.replace(/\s*\{.*/g, '');
  return solution;
}

function extractNumericalSettings(string) {
  var settings = string.match(/\{.*\}/g);
  if(settings) {
    settings = settings[0].replace(/\{|\}/g, '');
    settings = settings.split(/\,\s*/g);
  }
  return settings;
}

function onEditorButton(e) {
  e.preventDefault();

  switch($(this).attr('class')) {
    case 'multiple-choice-button':
      makeMultipleChoice();
      break;
    case 'string-button':
      makeStringInput();
      break;
    case 'number-button':
      makeNumberInput();
      break;
    case 'checks-button':
      makeCheckboxes();
      break;
    case 'dropdown-button':
      makeSelect();
      break;
  }
}

function newUnit() {
  window.location = 'index.html';
}

function makeHeader() {
  var selection = simpleEditor.getSelection();
  var revisedSelection = selection + '\n';
  for(var i = 0; i < selection.length; i++) {
    revisedSelection += '=';
  }
  simpleEditor.replaceSelection(revisedSelection);
}

function makeVideo() {
  var selection = simpleEditor.getSelection();
  simpleEditor.replaceSelection('{{video ' + selection + '}}');
}

function makeMultipleChoice() {
  console.log(currentEditor);
  var selection = simpleEditor.getSelection();
  if(selection.length > 0) {
    var cleanSelection = selection.replace(/\n\n/g, '\n');
    var lines = cleanSelection.split('\n');
    var revisedLines = '';
    for(var i = 0; i < lines.length; i++) {
      revisedLines += '(';
      if(/x\s/i.test(lines[i])) {
        revisedLines += 'x';
        lines[i] = lines[i].replace(/x\s/i, '');
      } else {
        revisedLines += ' ';
      }
      revisedLines += ') ' + lines[i] + '\n';
    }
    simpleEditor.replaceSelection(revisedLines);
  } else {
    var template = '( ) incorrect\n';
    template += '( ) incorrect\n';
    template += '(x) correct\n';
    simpleEditor.replaceSelection(template);
    setFocus();
  }
}

function makeStringInput() {
  var selection = simpleEditor.getSelection();
  if(selection.length > 0) {
    var revisedSelection = '___[' + selection + ']';
  simpleEditor.replaceSelection(revisedSelection);
  } else {
    var template = '___[answer]\n';
    simpleEditor.replaceSelection(template);
    setFocus();
  }
}

function makeNumberInput() {
  var selection = simpleEditor.getSelection();
  if(selection.length > 0) {
    var revisedSelection = '###[' + selection + ']';
    simpleEditor.replaceSelection(revisedSelection);
  } else {
    var template = '###[answer +-tolerance]\n';
    simpleEditor.replaceSelection(template);
    setFocus();
  }
}

function makeCheckboxes() {
  var selection = simpleEditor.getSelection();
  if(selection.length > 0) {
    var cleanSelection = selection.replace(/\n\n/g, '\n');
    var lines = cleanSelection.split('\n');
    var revisedLines = '';
    for(var i = 0; i < lines.length; i++) {
      revisedLines += '[';
      if(/x\s/i.test(lines[i])) {
        revisedLines += 'x';
        lines[i] = lines[i].replace(/x\s/i, '');
      } else {
        revisedLines += ' ';
      }
      revisedLines += '] ' + lines[i] + '\n';
    }
    simpleEditor.replaceSelection(revisedLines);
  } else {
    var template = '[x] correct\n';
    template += '[ ] incorrect\n';
    template += '[x] correct\n';
    simpleEditor.replaceSelection(template);
    setFocus();
  }
}

function makeSelect() {
  var selection = simpleEditor.getSelection();
  if(selection.length > 0) {
    var revisedSelection = '[[' + selection + ']]';
    simpleEditor.replaceSelection(revisedSelection);
  } else {
    var template = '[[incorrect, (correct), incorrect]]\n';
    simpleEditor.replaceSelection(template);
    setFocus();
  }
}

function onKeyboard(e) {
  switch(e.keyCode) {
    // n
    case 78:
      if(e.ctrlKey) {
        e.preventDefault();
        newUnit();
      }
      break;
  }     
}