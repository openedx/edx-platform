class @MarkdownEditingDescriptor extends XModule.Descriptor
  # TODO really, these templates should come from or also feed the cheatsheet
  @multipleChoiceTemplate : "( ) incorrect\n( ) incorrect\n(x) correct\n"
  @checkboxChoiceTemplate: "[x] correct\n[ ] incorrect\n[x] correct\n"
  @stringInputTemplate: "= answer\n"
  @numberInputTemplate: "= answer +- 0.001%\n"
  @selectTemplate: "[[incorrect, (correct), incorrect]]\n"
  @headerTemplate: "Header\n=====\n"
  @explanationTemplate: "[explanation]\nShort explanation\n[explanation]\n"

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
      # Need to refresh to get line numbers to display properly (and put cursor position to 0)
      @xml_editor.setCursor(0)
      @xml_editor.refresh()
      # Hide markdown-specific toolbar buttons
      $(@element.find('.editor-bar')).hide()

  ###
  Have the user confirm the one-way conversion to XML.
  Returns true if the user clicked OK, else false.
  ###
  confirmConversionToXml: ->
    # TODO: use something besides a JavaScript confirm dialog?
    return confirm("If you use the Advanced Editor, this problem will be converted to XML and you will not be able to return to the Simple Editor Interface.\n\nProceed to the Advanced Editor and convert this problem to XML?")

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
            metadata:
            	markdown: @markdown_editor.getValue()
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

# We may wish to add insertHeader. Here is Tom's code.
# function makeHeader() {
#  var selection = simpleEditor.getSelection();
#  var revisedSelection = selection + '\n';
#  for(var i = 0; i < selection.length; i++) {
#revisedSelection += '=';
#  }
#  simpleEditor.replaceSelection(revisedSelection);
#}
#




  @parseForQuestionHints: (answerString) ->
    # parse a single answer string for any hint text associated with this single answer item
    feedbackString = ''
    matchString = ''
    matches = answerString.match( /{{(.+)}}/ )       # string surrounded by {{...}} is a match group
    if matches
        matchString = matches[0]        # group 0 holds the entire matching string (includes delimiters)
        feedbackString = matches[1]     # group 1 holds the matching characters (our string)
        answerString = answerString.replace(matchString, '')

    MarkdownEditingDescriptor.questionHintStrings.push(feedbackString)  # add a feedback string entry (possibly null)
    MarkdownEditingDescriptor.questionHintMatches.push(matchString)     # add a match string entry (possibly null)
    return answerString

  @parseForProblemHints: (xmlString) ->
    for line in xmlString.split('\n')
      matches = line.match( /\|\|(.+)\|\|/ )      # string surrounded by ||...|| is a match group
      if matches
        problemHint = matches[1]
        MarkdownEditingDescriptor.problemHintsStrings.push(problemHint)
        xmlString = xmlString.replace(matches[0], '')                     # strip out the matched text from the xml
    return xmlString;

  @parseForCompoundConditionHints: (xmlString) ->
    for line in xmlString.split('\n')
      matches = line.match( /\{\{(.+)\}\}/ )      # string surrounded by {{...}} is a match group
      if matches
        questionHintString = matches[1]
        splitMatches = questionHintString.match(  /\(\((.+)\)\)(.+)/)    # surrounded by ((...)) is a boolean condition
        if splitMatches
          booleanExpression = splitMatches[1]
          hintText = splitMatches[2]
          MarkdownEditingDescriptor.problemHintsBooleanStrings.push(hintText)
          MarkdownEditingDescriptor.problemHintsBooleanExpressions.push(booleanExpression)
    return xmlString;

  @insertBooleanHints: (xmlStringUnderConstruction) ->
    index = 0
    for booleanExpression in MarkdownEditingDescriptor.problemHintsBooleanExpressions
      hintText = MarkdownEditingDescriptor.problemHintsBooleanStrings[index]
      booleanHintElement  = '        <booleanhint value="' + booleanExpression + '">' + hintText + '\n'
      booleanHintElement += '        </booleanhint>\n'
      xmlStringUnderConstruction += booleanHintElement
      index = index + 1
    return xmlStringUnderConstruction



  @parseForCheckbox: (xmlString) ->
    isCheckboxType = false

    returnXmlString =  '    <choiceresponse>\n'
    returnXmlString += '        <checkboxgroup direction="vertical">\n'

    for line in xmlString.split('\n')
      hintText = ''
      correctnessText = ''
      itemText = ''
      choiceMatches = line.match( /\s+\[\s*x?\s*\][^\n]+/ )
      if choiceMatches                          # this line includes '[...]' so it must be a checkbox choice
        isCheckboxType = true
        hintMatches = line.match( /{{(.+)}}/ )  # extract the {{...}} phrase, if any
        if hintMatches
          matchString = hintMatches[0]          # group 0 holds the entire matching string (includes delimiters)
          hintText = hintMatches[1].trim()      # group 1 holds the matching characters (our string)
          line = line.replace(matchString, '')  # remove the {{...}} phrase, else it will be displayed to student


        itemMatches = line.match( /(\s+\[\s*x?\s*\])(.+)[^\n]+/ )
        if itemMatches
          correctnessText = 'False'
          if itemMatches[1].match(/X/i)
            correctnessText = 'True'
          correctnessTextList = correctnessText
          itemText = itemMatches[2].trim()

        returnXmlString += '          <choice  correct="' + correctnessText + '">'
        returnXmlString += '              ' + itemText + '\n'
        if hintText
          returnXmlString += '               <choicehint>' + hintText + '\n'
          returnXmlString += '               </choicehint>\n'
        returnXmlString += '          </choice>\n'

    returnXmlString += '        </checkboxgroup>\n'

    MarkdownEditingDescriptor.parseForCompoundConditionHints(xmlString);  # pull out any compound condition hints
    returnXmlString = MarkdownEditingDescriptor.insertBooleanHints(returnXmlString);

    returnXmlString += '    </choiceresponse>\n'

    if not isCheckboxType
      returnXmlString = xmlString

    return returnXmlString














  @markdownToXml: (markdown)->
    toXml = `function (markdown) {
      var xml = markdown,
          i, splits, scriptFlag;

      // replace headers
      xml = xml.replace(/(^.*?$)(?=\n\=\=+$)/gm, '<h1>$1</h1>');
      xml = xml.replace(/\n^\=\=+$/gm, '');

      // initialize the targeted feedback working arrays
      MarkdownEditingDescriptor.questionHintStrings = [];
      MarkdownEditingDescriptor.questionHintMatches = [];
      MarkdownEditingDescriptor.problemHintsStrings = [];
      MarkdownEditingDescriptor.problemHintsBooleanExpressions = [];
      MarkdownEditingDescriptor.problemHintsBooleanStrings = [];

      xml = MarkdownEditingDescriptor.parseForProblemHints(xml);      // pull out any problem hints
      debugger;
      xml = MarkdownEditingDescriptor.parseForCheckbox(xml);          // examine the string for a checkbox problem
      debugger;

      // group multiple choice answers
      xml = xml.replace(/(^\s*\(.{0,3}\).*?$\n*)+/gm, function(match, p) {
      var choices = '';
      var shuffle = false;
      var options = match.split('\n');
      for(var i = 0; i < options.length; i++) {
          if(options[i].length > 0) {

            options[i] = MarkdownEditingDescriptor.parseForQuestionHints(options[i]);
            hintString = String(MarkdownEditingDescriptor.questionHintStrings[i]);
            hintElement = '';
            if (hintString.length > 0) {
              hintElement = '\n            <choicehint> ' + hintString + ' </choicehint>\n';
            }



            var value = options[i].split(/^\s*\(.{0,3}\)\s*/)[1];
            var inparens = /^\s*\((.{0,3})\)\s*/.exec(options[i])[1];
            var correct = 'False';
            if(/x/i.test(inparens)) {
              correct = 'True';
            }

            var fixed = '';
            if(/@/.test(inparens)) {
              fixed = ' fixed="true"';
            }
            if(/!/.test(inparens)) {
              shuffle = true;
            }
            choices += '        <choice correct="' + correct + '"' + fixed + '>' + value + hintElement + '        </choice>\n';
          }
        }
        var result = '    <multiplechoiceresponse>\n';
        if(shuffle) {
          result += '        <choicegroup type="MultipleChoice" shuffle="true">\n';
        } else {
          result += '        <choicegroup type="MultipleChoice">\n';
        }
        result += choices;
        result += '        </choicegroup>\n';
        result += '    </multiplechoiceresponse>\n\n';

        return result;
      });


//
//
//
//      xml = xml.replace(/(\s+\[\s*x?\s*\].+{\n)+/g, function(match) {
//          var groupString = '    <choiceresponse>\n',
//              options, value, correct;
//
//          confirm('115 - ' + match)
//          groupString += '        <checkboxgroup direction="vertical">\n';
//          options = match.split('\n');
//          confirm('107 - ' + options[0])
//
//          for (i = 0; i < options.length; i += 1) {
//              if(options[i].length > 0) {
//                  options[i] = MarkdownEditingDescriptor.parseForQuestionHints(options[i]);
//                  hintString = String(MarkdownEditingDescriptor.questionHintStrings[i]);
//                  hintElement = '';
//                  if (hintString.length > 0) {
//                    hintElement = '\n            <choicehint> ' + hintString + ' </choicehint>\n';
//                  }
//                  value = options[i].split(/^\s*\[.?\]\s*/)[1];
//                  correct = /^\s*\[x\]/i.test(options[i]);
//                  groupString += '        <choice  correct="' + correct + '">' + value + hintElement + '        </choice>\n';
//               }
//          }
//
//          groupString += '        </checkboxgroup>\n';
//          groupString += '    </choiceresponse>\n\n';
//          groupString = MarkdownEditingDescriptor.insertBooleanHints(groupString);
//
//          return groupString;
//      });

      // replace string and numerical
      xml = xml.replace(/(^\=\s*(.*?$)(\n*or\=\s*(.*?$))*)+/gm, function(match, p) {
          // Split answers
          var answersList = p.replace(/^(or)?=\s*/gm, '').split('\n'),

              processNumericalResponse = function (value) {
                  var params, answer, string;

                  if (_.contains([ '[', '(' ], value[0]) && _.contains([ ']', ')' ], value[value.length-1]) ) {
                    // [5, 7) or (5, 7), or (1.2345 * (2+3), 7*4 ]  - range tolerance case
                    // = (5*2)*3 should not be used as range tolerance
                    string = '<numericalresponse answer="' + value +  '">\n';
                    string += '  <formulaequationinput />\n';
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
                  string += '</numericalresponse>\n\n';

                  return string;
              },

              processStringResponse = function (values) {
                  var firstAnswer = values.shift(), string;

                  if (firstAnswer[0] === '|') { // this is regexp case
                      string = '<stringresponse answer="' + firstAnswer.slice(1).trim() +  '" type="ci regexp" >\n';
                  } else {
                      string = '<stringresponse answer="' + firstAnswer +  '" type="ci" >\n';
                  }

                  for (i = 0; i < values.length; i += 1) {
                      string += '  <additional_answer>' + values[i] + '</additional_answer>\n';
                  }

                  string +=  '  <textline size="20"/>\n</stringresponse>\n\n';

                  return string;
              };

          return processNumericalResponse(answersList[0]) || processStringResponse(answersList);
      });

      // replace selects
      xml = xml.replace(/\[\[(.+?)\]\]/g, function(match, p) {
          var selectString = '\n<optionresponse>\n',
              correct, options;

          selectString += '  <optioninput options="(';
          options = p.split(/\,\s*/g);

          for (i = 0; i < options.length; i += 1) {
              selectString += "'" + options[i].replace(/(?:^|,)\s*\((.*?)\)\s*(?:$|,)/g, '$1') + "'" + (i < options.length -1 ? ',' : '');
          }

          selectString += ')" correct="';
          correct = /(?:^|,)\s*\((.*?)\)\s*(?:$|,)/g.exec(p);

          if (correct) {
              selectString += correct[1];
          }

          selectString += '"></optioninput>\n';
          selectString += '</optionresponse>\n\n';

          return selectString;
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

      // surround w/ problem tag
      xml = '<problem schema="edXML/1.0">\n' + xml + '\n</problem>';

      return xml;
    }`
    return toXml markdown

