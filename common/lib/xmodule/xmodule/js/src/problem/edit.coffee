# Coffeescript markdown support.
# Most of the functionality is in the markdownToXml function,
# which in fact is regular javascript within backticks.

class @MarkdownEditingDescriptor extends XModule.Descriptor
  # TODO really, these templates should come from or also feed the cheatsheet
  @multipleChoiceTemplate : "( ) #{gettext 'incorrect'}\n( ) #{gettext 'incorrect'}\n(x) #{gettext 'correct'}\n"
  @checkboxChoiceTemplate: "[x] #{gettext 'correct'}\n[ ] incorrect\n[x] correct\n"
  @stringInputTemplate: "= #{gettext 'answer'}\n"
  @numberInputTemplate: "= #{gettext 'answer'} +- 0.001%\n"
  @selectTemplate: "[[#{gettext 'incorrect'}, (#{gettext 'correct'}), #{gettext 'incorrect'}]]\n"
  @headerTemplate: "#{gettext 'Header'}\n=====\n"
  @explanationTemplate: "[explanation]\n#{gettext 'Short explanation'}\n[explanation]\n"

  constructor: (element) ->
    @element = element

    if $(".markdown-box", @element).length != 0
      @markdown_editor = CodeMirror.fromTextArea($(".markdown-box", element)[0], {
      lineWrapping: true
      mode: null
      })
      @setCurrentEditor(@markdown_editor)
      # Add listeners for toolbar buttons (only present for markdown editor)
      @element.on('click', '.xml-tab', @onShowXMLButton)
      @element.on('click', '.format-buttons a', @onToolbarButton)
      @element.on('click', '.cheatsheet-toggle', @toggleCheatsheet)
      # Hide the XML text area
      $(@element.find('.xml-box')).hide()
    else
      @createXMLEditor()

  ###
  Creates the XML Editor and sets it as the current editor. If text is passed in,
  it will replace the text present in the HTML template.

  text: optional argument to override the text passed in via the HTML template
  ###
  createXMLEditor: (text) ->
    @xml_editor = CodeMirror.fromTextArea($(".xml-box", @element)[0], {
    mode: "xml"
    lineNumbers: true
    lineWrapping: true
    })
    if text
      @xml_editor.setValue(text)
    @setCurrentEditor(@xml_editor)
    $(@xml_editor.getWrapperElement()).toggleClass("CodeMirror-advanced");
    # Need to refresh to get line numbers to display properly.
    @xml_editor.refresh()

  ###
  User has clicked to show the XML editor. Before XML editor is swapped in,
  the user will need to confirm the one-way conversion.
  ###
  onShowXMLButton: (e) =>
    e.preventDefault();
    if @cheatsheet && @cheatsheet.hasClass('shown')
      @cheatsheet.toggleClass('shown')
      @toggleCheatsheetVisibility()
    if @confirmConversionToXml()
      @createXMLEditor(MarkdownEditingDescriptor.markdownToXml(@markdown_editor.getValue()))
      # Put cursor position to 0.
      @xml_editor.setCursor(0)
      # Hide markdown-specific toolbar buttons
      $(@element.find('.editor-bar')).hide()

  ###
  Have the user confirm the one-way conversion to XML.
  Returns true if the user clicked OK, else false.
  ###
  confirmConversionToXml: ->
    # TODO: use something besides a JavaScript confirm dialog?
    return confirm(gettext "If you use the Advanced Editor, this problem will be converted to XML and you will not be able to return to the Simple Editor Interface.\n\nProceed to the Advanced Editor and convert this problem to XML?")

  ###
  Event listener for toolbar buttons (only possible when markdown editor is visible).
  ###
  onToolbarButton: (e) =>
    e.preventDefault();
    selection = @markdown_editor.getSelection()
    revisedSelection = null
    switch $(e.currentTarget).attr('class')
      when "multiple-choice-button" then revisedSelection = MarkdownEditingDescriptor.insertMultipleChoice(selection)
      when "string-button" then revisedSelection = MarkdownEditingDescriptor.insertStringInput(selection)
      when "number-button" then revisedSelection = MarkdownEditingDescriptor.insertNumberInput(selection)
      when "checks-button" then revisedSelection = MarkdownEditingDescriptor.insertCheckboxChoice(selection)
      when "dropdown-button" then revisedSelection = MarkdownEditingDescriptor.insertSelect(selection)
      when "header-button" then revisedSelection = MarkdownEditingDescriptor.insertHeader(selection)
      when "explanation-button" then revisedSelection = MarkdownEditingDescriptor.insertExplanation(selection)
      else # ignore click

    if revisedSelection != null
      @markdown_editor.replaceSelection(revisedSelection)
      @markdown_editor.focus()

  ###
  Event listener for toggling cheatsheet (only possible when markdown editor is visible).
  ###
  toggleCheatsheet: (e) =>
    e.preventDefault();
    if !$(@markdown_editor.getWrapperElement()).find('.simple-editor-cheatsheet')[0]
      @cheatsheet = $($('#simple-editor-cheatsheet').html())
      $(@markdown_editor.getWrapperElement()).append(@cheatsheet)

    @toggleCheatsheetVisibility()

    setTimeout (=> @cheatsheet.toggleClass('shown')), 10


  ###
  Function to toggle cheatsheet visibility.
  ###
  toggleCheatsheetVisibility: () =>
    $('.modal-content').toggleClass('cheatsheet-is-shown')

  ###
  Stores the current editor and hides the one that is not displayed.
  ###
  setCurrentEditor: (editor) ->
    if @current_editor
      $(@current_editor.getWrapperElement()).hide()
    @current_editor = editor
    $(@current_editor.getWrapperElement()).show()
    $(@current_editor).focus();

  ###
  Called when save is called. Listeners are unregistered because editing the block again will
  result in a new instance of the descriptor. Note that this is NOT the case for cancel--
  when cancel is called the instance of the descriptor is reused if edit is selected again.
  ###
  save: ->
    @element.off('click', '.xml-tab', @changeEditor)
    @element.off('click', '.format-buttons a', @onToolbarButton)
    @element.off('click', '.cheatsheet-toggle', @toggleCheatsheet)
    if @current_editor == @markdown_editor
        {
            data: MarkdownEditingDescriptor.markdownToXml(@markdown_editor.getValue())
            metadata: markdown: @markdown_editor.getValue()
        }
    else
       {
          data: @xml_editor.getValue()
          nullout: ['markdown']
       }

  @insertMultipleChoice: (selectedText) ->
    return MarkdownEditingDescriptor.insertGenericChoice(selectedText, '(', ')', MarkdownEditingDescriptor.multipleChoiceTemplate)

  @insertCheckboxChoice: (selectedText) ->
    return MarkdownEditingDescriptor.insertGenericChoice(selectedText, '[', ']', MarkdownEditingDescriptor.checkboxChoiceTemplate)

  @insertGenericChoice: (selectedText, choiceStart, choiceEnd, template) ->
    if selectedText.length > 0
      # Replace adjacent newlines with a single newline, strip any trailing newline
      cleanSelectedText = selectedText.replace(/\n+/g, '\n').replace(/\n$/,'')
      lines =  cleanSelectedText.split('\n')
      revisedLines = ''
      for line in lines
        revisedLines += choiceStart
        # a stand alone x before other text implies that this option is "correct"
        if /^\s*x\s+(\S)/i.test(line)
          # Remove the x and any initial whitespace as long as there's more text on the line
          line = line.replace(/^\s*x\s+(\S)/i, '$1')
          revisedLines += 'x'
        else
          revisedLines += ' '
        revisedLines += choiceEnd + ' ' + line + '\n'
      return revisedLines
    else
      return template

  @insertStringInput: (selectedText) ->
    return MarkdownEditingDescriptor.insertGenericInput(selectedText, '= ', '', MarkdownEditingDescriptor.stringInputTemplate)

  @insertNumberInput: (selectedText) ->
    return MarkdownEditingDescriptor.insertGenericInput(selectedText, '= ', '', MarkdownEditingDescriptor.numberInputTemplate)

  @insertSelect: (selectedText) ->
    return MarkdownEditingDescriptor.insertGenericInput(selectedText, '[[', ']]', MarkdownEditingDescriptor.selectTemplate)

  @insertHeader: (selectedText) ->
    return MarkdownEditingDescriptor.insertGenericInput(selectedText, '', '\n====\n', MarkdownEditingDescriptor.headerTemplate)

  @insertExplanation: (selectedText) ->
    return MarkdownEditingDescriptor.insertGenericInput(selectedText, '[explanation]\n', '\n[explanation]', MarkdownEditingDescriptor.explanationTemplate)

  @insertGenericInput: (selectedText, lineStart, lineEnd, template) ->
    if selectedText.length > 0
      # TODO: should this insert a newline afterwards?
      return lineStart + selectedText + lineEnd
    else
      return template


  @markdownToXml: (markdown)->
    toXml = `function (markdown) {
      var xml = markdown,
          i, splits, scriptFlag;

      // fix DOS \r\n line endings to look like \n
      xml = xml.replace(/\r\n/g, '\n');

      // replace headers
      xml = xml.replace(/(^.*?$)(?=\n\=\=+$)/gm, '<h1>$1</h1>');
      xml = xml.replace(/\n^\=\=+$/gm, '');

      // Pull out demand hints,  || a hint ||
      var demandhints = '';
      xml = xml.replace(/(^\s*\|\|.*?\|\|\s*$\n?)+/gm, function(match) {  // $\n
          var options = match.split('\n');
          for (i = 0; i < options.length; i += 1) {
              var inner = /\s*\|\|(.*?)\|\|/.exec(options[i]);
              if (inner) {
                  demandhints += '  <hint>' + inner[1].trim() + '</hint>\n';
              }
           }
           return '';
      });

      // replace \n+whitespace within extended hint {{ .. }}, by a space, so the whole
      // hint sits on one line.
      // This is the one instance of {{ ... }} matching that permits \n
      xml = xml.replace(/{{(.|\n)*?}}/gm, function(match) {
          return match.replace(/\r?\n( |\t)*/g, ' ');
      });

      // Function used in many places to extract {{ label:: a hint }}.
      // Returns a little hash with various parts of the hint:
      // hint: the hint or empty, nothint: the rest
      // labelassign: javascript assignment of label attribute, or empty
      extractHint = function(text, detectParens) {
          var curly = /\s*{{(.*?)}}/.exec(text);
          var hint = '';
          var label = '';
          var parens = false;
          var labelassign = '';
          if (curly) {
              text = text.replace(curly[0], '');
              hint = curly[1].trim();
              var labelmatch = /^(.*?)::/.exec(hint);
              if (labelmatch) {
                  hint = hint.replace(labelmatch[0], '').trim();
                  label = labelmatch[1].trim();
                  labelassign = ' label="' + label + '"';
              }
           }
           if (detectParens) {
             if (text.length >= 2 && text[0] == '(' && text[text.length-1] == ')') {
                 text = text.substring(1, text.length-1)
                 parens = true;
              }
           }
           return {'nothint': text, 'hint': hint, 'label': label, 'parens': parens, 'labelassign': labelassign};
      }


      // replace selects
      // [[ a, b, (c) ]]
      // [[
      //     a
      //     b
      //     (c)
      //  ]]
      // <optionresponse>
      //  <optioninput>
      //     <option  correct="True">AAA<optionhint  label="Good Job">Yes, multiple choice is the right answer.</optionhint> 
      // Note: part of the option-response syntax looks like multiple-choice, so it must be processed first.   
      xml = xml.replace(/\[\[((.|\n)+?)\]\]/g, function(match, group1) {
          // decide if this is old style or new style
          if (match.indexOf('\n') == -1) {  // OLD style, [[ .... ]]  on one line
              var options = group1.split(/\,\s*/g);
              var optiontag = '  <optioninput options="(';
              for (i = 0; i < options.length; i += 1) {
                  optiontag += "'" + options[i].replace(/(?:^|,)\s*\((.*?)\)\s*(?:$|,)/g, '$1') + "'" + (i < options.length -1 ? ',' : '');
              }
              optiontag += ')" correct="';
              var correct = /(?:^|,)\s*\((.*?)\)\s*(?:$|,)/g.exec(group1);
              if (correct) {
                  optiontag += correct[1];
              }
              optiontag += '">';
              return '\n<optionresponse>\n' + optiontag + '</optioninput>\n</optionresponse>\n\n';
          }

          // new style  [[ many-lines ]]
          var lines = group1.split('\n');
          var optionlines = ''
          for (i = 0; i < lines.length; i++) {
              var line = lines[i].trim();
              if (line.length > 0) {
                  var textHint = extractHint(line, true);
                  var correctstr = ' correct="' + (textHint.parens?'True':'False') + '"';
                  var hintstr = '';
                  if (textHint.hint) {
                      var label = textHint.label;
                      if (label) {
                          label = ' label="' + label + '"';
                      }
                      hintstr = ' <optionhint' + label + '>' + textHint.hint + '</optionhint>';
                  }
                  optionlines += '    <option' + correctstr + '>' + textHint.nothint + hintstr + '</option>\n'
               }
           }
          return '\n<optionresponse>\n  <optioninput>\n' + optionlines + '  </optioninput>\n</optionresponse>\n\n';
      });

      //_____________________________________________________________________
      //
      // multiple choice questions
      //
      xml = xml.replace(/(^\s*\(.{0,3}\).*?$\n*)+/gm, function(match, p) {
        var choices = '';
        var shuffle = false;
        var options = match.split('\n');
        for(var i = 0; i < options.length; i++) {
          options[i] = options[i].trim();                   // trim off leading/trailing whitespace
          if(options[i].length > 0) {
            var value = options[i].split(/^\s*\(.{0,3}\)\s*/)[1];
            var inparens = /^\s*\((.{0,3})\)\s*/.exec(options[i])[1];
            var correct = /x/i.test(inparens);
            var fixed = '';
            if(/@/.test(inparens)) {
              fixed = ' fixed="true"';
            }
            if(/!/.test(inparens)) {
              shuffle = true;
            }

            var hint = extractHint(value);
            if (hint.hint) {
              value = hint.nothint;
              value = value + ' <choicehint' + hint.labelassign + '>' + hint.hint + '</choicehint>';
            }
            choices += '    <choice correct="' + correct + '"' + fixed + '>' + value + '</choice>\n';
          }
        }
        var result = '<multiplechoiceresponse>\n';
        if(shuffle) {
          result += '  <choicegroup type="MultipleChoice" shuffle="true">\n';
        } else {
          result += '  <choicegroup type="MultipleChoice">\n';
        }
        result += choices;
        result += '  </choicegroup>\n';
        result += '</multiplechoiceresponse>\n\n';
        return result;
      });

      // group check answers
      // [.] with {{...}} lines mixed in
      xml = xml.replace(/(^\s*((\[.?\])|({{.*?}})).*?$\n*)+/gm, function(match) {
          var groupString = '<choiceresponse>\n',
              options, value, correct;

          groupString += '  <checkboxgroup>\n';
          options = match.split('\n');
          
          endHints = '';  // save these up to emit at the end

          for (i = 0; i < options.length; i += 1) {
              if(options[i].trim().length > 0) {
                  // detect the {{ ((A*B)) ...}} case first
                  // emits: <compoundhint value="A*B">AB hint</compoundhint>
                                    
                  var abhint = /^\s*{{\s*\(\((.*?)\)\)(.*?)}}/.exec(options[i]);
                  if (abhint) {
                       // lone case of hint text processing outside of extractHint, since syntax here is unique
                       var hintbody = abhint[2];
                       hintbody = hintbody.replace('&lf;', '\n').trim()
                       endHints += '    <compoundhint value="' + abhint[1].trim() +'">' + hintbody + '</compoundhint>\n';
                       continue;  // bail
                   }

                  value = options[i].split(/^\s*\[.?\]\s*/)[1];
                  correct = /^\s*\[x\]/i.test(options[i]);
                  hints = '';
                  //  {{ selected: You’re right that apple is a fruit. }, {unselected: Remember that apple is also a fruit.}}
                  var hint = extractHint(value);
                  if (hint.hint) {
                      var inner = '{' + hint.hint + '}';  // parsing is easier if we put outer { } back
                      var select = /{\s*(s|selected):((.|\n)*?)}/i.exec(inner);  // include \n since we are downstream of extractHint()
                      // checkbox choicehints get their own line, since there can be two of them
                      // <choicehint selected="true">You’re right that apple is a fruit.</choicehint>
                      if (select) {
                          hints += '\n      <choicehint selected="true">' + select[2].trim() + '</choicehint>';
                      }
                      var select = /{\s*(u|unselected):((.|\n)*?)}/i.exec(inner);
                      if (select) {
                          hints += '\n      <choicehint selected="false">' + select[2].trim() + '</choicehint>';
                      }
                      
                      // Blank out the original text only if the specific "selected" syntax is found
                      // That way, if the user types it wrong, at least they can see it's not processed.
                      if (hints) {
                          value = hint.nothint;
                      }
                  }
                  groupString += '    <choice correct="' + correct + '">' + value + hints +'</choice>\n';
              }
          }

          groupString += endHints;
          groupString += '  </checkboxgroup>\n';
          groupString += '</choiceresponse>\n\n';

          return groupString;
      });


      // replace string and numerical, numericalresponse, stringresponse
      // A fine example of the function-composition programming style.
      xml = xml.replace(/(^s?\=\s*(.*?$)(\n*(or|not)\=\s*(.*?$))*)+/gm, function(match, p) {
          // Line split here, trim off leading xxx= in each function
          var answersList = p.split('\n'),

              processNumericalResponse = function (value) {
                  // Numeric case is just a plain leading = with a single answer
                  value = value.replace(/^\=\s*/, '');
                  var params, answer, string;

                  var textHint = extractHint(value);
                  var hintLine = '';
                  if (textHint.hint) {
                    value = textHint.nothint;
                    hintLine = '  <correcthint' + textHint.labelassign + '>' + textHint.hint + '</correcthint>\n'
                  }

                  if (_.contains([ '[', '(' ], value[0]) && _.contains([ ']', ')' ], value[value.length-1]) ) {
                    // [5, 7) or (5, 7), or (1.2345 * (2+3), 7*4 ]  - range tolerance case
                    // = (5*2)*3 should not be used as range tolerance
                    string = '<numericalresponse answer="' + value +  '">\n';
                    string += '  <formulaequationinput />\n';
                    string += hintLine;
                    string += '</numericalresponse>\n\n';
                    return string;
                  }

                  if (isNaN(parseFloat(value))) {
                      return false;
                  }

                  // Tries to extract parameters from string like 'expr +- tolerance'
                  params = /(.*?)\+\-\s*(.*?$)/.exec(value);

                  if(params) {
                      answer = params[1].replace(/\s+/g, ''); // support inputs like 5*2 +- 10
                      string = '<numericalresponse answer="' + answer + '">\n';
                      string += '  <responseparam type="tolerance" default="' + params[2] + '" />\n';
                  } else {
                      answer = value.replace(/\s+/g, ''); // support inputs like 5*2
                      string = '<numericalresponse answer="' + answer + '">\n';
                  }

                  string += '  <formulaequationinput />\n';
                  string += hintLine;
                  string += '</numericalresponse>\n\n';

                  return string;
              },

              processStringResponse = function (values) {
                  // First string case is s?=
                  var firstAnswer = values.shift(), string;
                  firstAnswer = firstAnswer.replace(/^s?\=\s*/, '');
                  var textHint = extractHint(firstAnswer);
                  firstAnswer = textHint.nothint;
                  var typ = ' type="ci"';
                  if (firstAnswer[0] == '|') { // this is regexp case
                      typ = ' type="ci regexp"';
                      firstAnswer = firstAnswer.slice(1).trim();
                  }
                  string = '<stringresponse answer="' + firstAnswer + '"' + typ + ' >\n';
                  if (textHint.hint) {
                      string += '  <correcthint' + textHint.labelassign + '>' + textHint.hint + '</correcthint>\n';
                  }

                  // Subsequent cases are not= or or=
                  for (i = 0; i < values.length; i += 1) {
                      var textHint = extractHint(values[i]);
                      var notMatch = /^not\=\s*(.*)/.exec(textHint.nothint);
                      if (notMatch) {
                          string += '  <stringequalhint answer="' + notMatch[1] + '"' + textHint.labelassign + '>' + textHint.hint + '</stringequalhint>\n';
                          continue;
                      }
                      var orMatch = /^or\=\s*(.*)/.exec(textHint.nothint);
                      if (orMatch) {
                          // additional_answer with answer= attribute
                          string += '  <additional_answer answer="' + orMatch[1] + '">';
                          if (textHint.hint) {
                              string += '<correcthint' + textHint.labelassign + '>' + textHint.hint + '</correcthint>';
                          }
                          string += '</additional_answer>\n';
                      }
                  }

                  string +=  '  <textline size="20"/>\n</stringresponse>\n\n';

                  return string;
              };

          return processNumericalResponse(answersList[0]) || processStringResponse(answersList);
      });

      
      // replace explanations
      xml = xml.replace(/\[explanation\]\n?([^\]]*)\[\/?explanation\]/gmi, function(match, p1) {
          var selectString = '<solution>\n<div class="detailed-solution">\nExplanation\n\n' + p1 + '\n</div>\n</solution>';

          return selectString;
      });
      
      // replace labels
      // looks for >>arbitrary text<< and inserts it into the label attribute of the input type directly below the text. 
      var split = xml.split('\n');
      var new_xml = [];
      var line, i, curlabel, prevlabel = '';
      var didinput = false;
      for (i = 0; i < split.length; i++) {
        line = split[i];
        if (match = line.match(/>>(.*)<</)) {
          curlabel = match[1].replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&apos;');
          line = line.replace(/>>|<</g, '');
        } else if (line.match(/<\w+response/) && didinput && curlabel == prevlabel) {
          // reset label to prevent gobbling up previous one (if multiple questions)
          curlabel = '';
          didinput = false;
        } else if (line.match(/<(textline|optioninput|formulaequationinput|choicegroup|checkboxgroup)/) && curlabel != '' && curlabel != undefined) {
          line = line.replace(/<(textline|optioninput|formulaequationinput|choicegroup|checkboxgroup)/, '<$1 label="' + curlabel + '"');
          didinput = true;
          prevlabel = curlabel;
        }
        new_xml.push(line);
      }
      xml = new_xml.join('\n');

      // replace code blocks
      xml = xml.replace(/\[code\]\n?([^\]]*)\[\/?code\]/gmi, function(match, p1) {
          var selectString = '<pre><code>\n' + p1 + '</code></pre>';

          return selectString;
      });

      // split scripts and preformatted sections, and wrap paragraphs
      splits = xml.split(/(\<\/?(?:script|pre).*?\>)/g);
      scriptFlag = false;

      for (i = 0; i < splits.length; i += 1) {
          if(/\<(script|pre)/.test(splits[i])) {
              scriptFlag = true;
          }

          if(!scriptFlag) {
              splits[i] = splits[i].replace(/(^(?!\s*\<|$).*$)/gm, '<p>$1</p>');
          }

          if(/\<\/(script|pre)/.test(splits[i])) {
              scriptFlag = false;
          }
      }

      xml = splits.join('');

      // rid white space
      xml = xml.replace(/\n\n\n/g, '\n');

      // if we've come across demand hints, wrap in <demandhint> at the end
      if (demandhints) {
          demandhints = '\n<demandhint>\n' + demandhints + '</demandhint>';
      }

      // make all elements descendants of a single problem element
      xml = '<problem>\n' + xml + demandhints + '\n</problem>';

      return xml;
    }`
    return toXml markdown

