class @MarkdownEditingDescriptor extends XModule.Descriptor
  # TODO really, these templates should come from or also feed the cheatsheet
  @multipleChoiceTemplate : "( ) incorrect\n( ) incorrect\n(x) correct\n"
  @checkboxChoiceTemplate: "[x] correct\n[ ] incorrect\n[x] correct\n"
  @stringInputTemplate: "= answer\n"
  @numberInputTemplate: "= answer +- 0.001_\n"
  @selectTemplate: "[[incorrect, (correct), incorrect]]\n"
  @headerTemplate: "Header\n=====\n"
  @explanationTemplate: "[explanation]\nShort explanation\n[explanation]\n"
  @customLabel: ""

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

#________________________________________________________________________________
  @matchCompoundConditionPattern: (testString) ->
    return testString.match( /\{\{(.+)\}\}/ )

#  #________________________________________________________________________________
#  @matchBooleanConditionPattern: (testString) ->
#    return testString.match( /\(\((.+)\)\)(.+)/ )

  #________________________________________________________________________________
  @matchMultipleChoicePattern: (testString) ->
    return testString.match( /\s+\(\s*x?\s*\)[^\n]+/ )

  #________________________________________________________________________________
  @matchCheckboxMarkerPattern: (testString) ->
    return testString.match( /(\s+\[\s*x?\s*\])([^\n]+)/ )

  #________________________________________________________________________________
  @insertParagraphText: (xmlString, reducedXmlString) ->
      returnXmlString = ''
      for line in reducedXmlString.split('\n')
        trimmedLine = line.trim()
        if trimmedLine.length > 0
          compoundConditionMatches = @matchCompoundConditionPattern( line )      # string surrounded by {{...}} is a match group
          if compoundConditionMatches == null
            returnXmlString += '<p>\n'
            returnXmlString += trimmedLine
            returnXmlString += '</p>\n'
      return returnXmlString

  #________________________________________________________________________________
  # check a hint string for a custom label (e.g., 'NOPE::you got this answer wrong')
  # if found, remove the label and the :: delimiter and save the label in the
  # 'customLabel' variable for later handling
  #
  @extractCustomLabel: (feedbackString) ->
    returnString = feedbackString                     # assume we will find no custom label
    tokens = feedbackString.split('::')
    if tokens.length > 1                              # check for a custom label to precede the feedback string
      @customLabel = ' label="' + tokens[0] + '"'    # save the custom label for insertion into the XML
      returnString = tokens[1]
    else
      @customLabel = ' '
    return returnString                               # return the feedback string but without the custom label, if any

  #________________________________________________________________________________
  # search for any text demarcated as a 'question hint' by the double braces {{..}}
  # if found, copy the text to an array for later insertion and remove that text
  # from the xmlString, replacing it with a unique marker for later restoration
  #
  @parseForQuestionHints: (xmlString) ->
    @questionHintStrings = []    # initialize the strings array

    DOUBLE_LEFT_BRACE_MARKER = '~~~'
    DOUBLE_RIGHT_BRACE_MARKER = '```'

    xmlString = xmlString.replace(/\{\{/g, DOUBLE_LEFT_BRACE_MARKER)   # replace all double left braces with '~~~~'
    xmlString = xmlString.replace(/}}/g, DOUBLE_RIGHT_BRACE_MARKER)    # replace all double right braces with '```'

    questionHintMatches = xmlString.match(/~~~[^`]+```/gm)
    if questionHintMatches
      index = 0
      for questionHintMatch in questionHintMatches
        xmlString = xmlString.replace( questionHintMatch, '_' + index++ + '_')
        questionHintMatch = questionHintMatch.replace(/~~~/gm, '')
        questionHintMatch = questionHintMatch.replace(/```/gm, '')
        @questionHintStrings.push(questionHintMatch)   # save the string but no delimiters

    return xmlString

  #________________________________________________________________________________
  # search for any text demarcated as a 'problem hint' by the double vertical bars
  # if found, copy the text to an array for later insertion and remove that text
  # from the xmlString
  #
  @parseForProblemHints: (xmlString) ->
    MarkdownEditingDescriptor.problemHintStrings = []    # initialize the strings array
    for line in xmlString.split('\n')
      matches = line.match( /\|\|(.+)\|\|/ )      # string surrounded by ||...|| is a match group
      if matches
        problemHint = matches[1]
        MarkdownEditingDescriptor.problemHintStrings.push(problemHint)
        xmlString = xmlString.replace(matches[0], '')                     # strip out the matched text from the xml
    return xmlString

  #________________________________________________________________________________
  # if any 'problem hint' entries were saved in the array, insert the 'demandhint'
  # element to the xml with a 'hint' element for each item
  #
  @insertProblemHints: (xmlStringUnderConstruction) ->
    if MarkdownEditingDescriptor.problemHintStrings
      if MarkdownEditingDescriptor.problemHintStrings.length > 0
        ondemandElement =  '    <demandhint>\n'
        for problemHint in MarkdownEditingDescriptor.problemHintStrings
          ondemandElement += '        <hint> ' +  problemHint + '\n'
          ondemandElement += '        </hint>\n'
        ondemandElement +=  '    </demandhint>\n'
        xmlStringUnderConstruction += ondemandElement
    return xmlStringUnderConstruction

  #________________________________________________________________________________
  # search for any commas found *within* a hint string (i.e., enclosed by the
  # {{...}} braces). if any are found, replace them by a very unique string (';;;')
  # so the parser won't get confused when a split on commas is performed. if
  # no such commas are found, try to replace the very unique string *back* to
  # a comma.
  #
  # the strategy here is to encapsulate this subsitution operation here in a
  # single bi-directional function to make it easier to understand what's
  # going on.
  #
  @substituteCommasInHints: (optionString) ->
    originalLength = optionString.length                                # save the starting length of the string

    newLength = 0
    while newLength != optionString.length                              # continue replacements until none are left
      newLength = optionString.length
      optionString = optionString.replace( /({{[^,]*),([^}]*}})/gm, '$1;;;$2')

    if optionString.length == originalLength                            # if we found no commas to replace
      optionString = optionString.replace( /;;;/gm, ',' )   # try the reverse replacment
    return optionString

  #________________________________________________________________________________
  @parseForDropdown: (xmlString) ->
    # parse the supplied string knowing it is a drop down problem
    dropdownMatches = xmlString.match( /\[\[([^\]]+)\]\]/ )   # try to match an opening and closing double bracket

    if dropdownMatches                            # the xml has an opening and closing double bracket [[...]]
      reducedXmlString = xmlString.replace(dropdownMatches[0], '')
      returnXmlString = MarkdownEditingDescriptor.insertParagraphText(xmlString, reducedXmlString)
      returnXmlString +=  '    <optionresponse>\n'
      returnXmlString += '        <optioninput options="OPTIONS_PLACEHOLDER" correct="CORRECT_PLACEHOLDER">\n'

      optionsString = ''
      delimiter = ''

      dropdownMatch = dropdownMatches[1]              # the match string is the entire set of drop down options
      dropdownMatch = @substituteCommasInHints(dropdownMatch)   # hide any in-hint commas

      for line in dropdownMatch.split( /[,\n]/)  # split the string between [[..]] brackets into single lines
        line = line.trim()
        line = @substituteCommasInHints(line)         # unhide any in-hint commas

        if line.length > 0
          hintText = ''
          correctnessText = ''
          itemText = ''
          hintMatches = line.match( /_([0-9]+)_/ ); # check for an extracted hint string
          if hintMatches                            # if we found one
            hintIndex = parseInt(hintMatches[1])
            hintText = MarkdownEditingDescriptor.questionHintStrings[ hintIndex ]
            hintText = hintText.trim()
            hintText = MarkdownEditingDescriptor.extractCustomLabel( hintText )
            line = line.replace(hintMatches[0], '')  # remove the hint marker, else it will be displayed

          correctChoiceMatch = line.match( /^\s*\(([^)]+)\)/ )  # try to match a parenthetical string: '(...)'
          if correctChoiceMatch                          # matched so this must be the correct answer
            correctnessText = 'True'
            itemText = correctChoiceMatch[1]
            returnXmlString = returnXmlString.replace('CORRECT_PLACEHOLDER', itemText)  # poke the correct value in
            optionsString += delimiter + '(' + itemText + ')'
          else
            correctnessText = 'False'
            itemText = line
            optionsString += delimiter + itemText.trim()

          if itemText[itemText.length-1] == ','     # check for an end-of-line comma
            itemText = itemText.slice(0, itemText.length-1) # suppress it
          itemText = itemText.trim()

          returnXmlString += '              <option  correct="' + correctnessText + '">'
          returnXmlString += '                  ' + itemText + '\n'
          if hintText
            returnXmlString += '                   <optionhint ' + @customLabel + '>' + hintText + '\n'
            returnXmlString += '                   </optionhint>\n'
          returnXmlString += '              </option>\n'

          delimiter = ', '

      returnXmlString += '        </optioninput>\n'
      returnXmlString = returnXmlString.replace('OPTIONS_PLACEHOLDER', optionsString)  # poke the options in
      returnXmlString += '    </optionresponse>\n'
    else
      returnXmlString = xmlString

    return returnXmlString

  #________________________________________________________________________________
  @parseForCheckbox: (xmlString) ->
    # parse the supplied string knowing it is a checkbox problem
    returnXmlString = ''
    reducedXmlString = ''
    booleanExpressionStrings = []
    booleanHintPhrases = []

    debugger

    returnXmlString +=  '    <choiceresponse>\n'
    returnXmlString += '        <checkboxgroup direction="vertical">\n'

    for line in xmlString.split('\n')
      correctnessText = ''
      itemText = ''
      hintTextSelected = ''
      hintTextUnselected = ''

      choiceMatches = @matchCheckboxMarkerPattern( line )
      if choiceMatches           # this line includes '[...]' so it must be a checkbox choice
        line = choiceMatches[2]  # remove the [..] phrase, else it will be displayed to student
        hintMatches = line.match( /_([0-9]+)_/ )  # check for an extracted hint string
        if hintMatches
          line = line.replace(hintMatches[0], '')  # remove the {{...}} phrase, else it will be displayed to student

          hintIndex = parseInt(hintMatches[1])
          combinedHintText = MarkdownEditingDescriptor.questionHintStrings[ hintIndex ]
          combinedHintText = combinedHintText.trim()
          combinedHintText = combinedHintText.replace( /(selected:|s:)/i, "S:")
          combinedHintText = combinedHintText.replace( /(unselected:|u:)/i, "U:")
          selectedMatches = combinedHintText.match(/\s*S:\s*([^}]+)/)
          unselectedMatches = combinedHintText.match(/\s*U:\s*([^}]+)/)

          if selectedMatches and unselectedMatches  # both a selected and unselected phrase were supplied for this choice
            hintTextSelected = selectedMatches[1]
            hintTextUnselected = unselectedMatches[1]

        correctnessText = 'False'
        if choiceMatches[1].match(/X/i)
          correctnessText = 'True'

        returnXmlString += '          <choice  correct="' + correctnessText + '">'
        returnXmlString += '              ' + line + '\n'
        if hintTextSelected.length > 0 and hintTextUnselected.length > 0
          returnXmlString += '               <choicehint selected="True">' + hintTextSelected + '\n'
          returnXmlString += '               </choicehint>\n'
          returnXmlString += '               <choicehint selected="False">' + hintTextUnselected + '\n'
          returnXmlString += '               </choicehint>\n'
        returnXmlString += '          </choice>\n'

      else                        # this line is not a checkbox choice, but it may be a combination hint spec line
        hintMatches = line.match( /_([0-9]+)_/ )  # check for an extracted hint string
        if hintMatches            # the line does contain an extracted hint string
          line = line.replace(hintMatches[0], '')  # remove the phrase, else it will be displayed to student
          hintIndex = parseInt(hintMatches[1])
          hintText = MarkdownEditingDescriptor.questionHintStrings[ hintIndex ]
          hintText = hintText.trim()
          combinationHintMatch = hintText.match( /\(\((.+)\)\)(.+)/ )
          if combinationHintMatch                   # the line does contain a combination hint phrase
            booleanExpressionStrings.push(combinationHintMatch[1])
            booleanHintPhrases.push(combinationHintMatch[2])

    returnXmlString += '        </checkboxgroup>\n'

    index = 0
    for booleanExpression in booleanExpressionStrings
      booleanHintPhrase = booleanHintPhrases[index++]
      returnXmlString += '        <booleanhint value="' + booleanExpression + '">' + booleanHintPhrase + '\n'
      returnXmlString += '        </booleanhint>\n'

    returnXmlString += '    </choiceresponse>\n'

    return returnXmlString

    
      #________________________________________________________________________________
  @parseForNumeric: (xmlString) ->
    # try to parse the supplied string to find a numeric problem
    # return the string unmodified if this is not a drop down problem
    returnXmlString = ''
    reducedXmlString = ''
    answerLines = []
    operator = ''
    answerExpression = ''
    answerString = ''
    plusMinus = ''
    tolerance = ''
    isNumeric = false
    responseParameterElementString = ''
    correctHintElementString = ''
    numericHintElementString = ''

    for line in xmlString.split('\n')
      numericMatch = line.match( /^\s*([=!]+)\s*([\d\.*/+-]+)\s+([+-]+)\s*([\d\.]+)/ )
      if numericMatch
        isNumeric = true
        answerLines.push(line)
      else
        reducedXmlString += line + '\n'

    if isNumeric                    # if this is a numeric problem
      for line in answerLines
        numericMatch = line.match( /^\s*([=!]+)\s*([\d\.*/+-]+)\s+([+-]+)\s*([\d\.]+)/ )
        if numericMatch
          if numericMatch[1]
            operator = numericMatch[1]
          if numericMatch[2]
            answerExpression = numericMatch[2]
          if numericMatch[3]
            plusMinus = numericMatch[3]
          if numericMatch[4]
            tolerance = numericMatch[4]

          if operator == '='
            if answerExpression
              if answerString == ''           # if this is the *first* answer supplied
                answerString = answerExpression
                if plusMinus and tolerance    # author has supplied a tolerance specification on the *first* answer
                  responseParameterElementString = '<responseparam type="tolerance" default="' + tolerance + '"/>\n'
                  hintMatches = line.match( /{{(.+)}}/ )  # extract the {{...}} phrase, if any
                  if hintMatches
                    hintText = hintMatches[1].trim()
                    correctHintElementString = "<correcthint>\n" + hintText + "\n</correcthint>\n"
                else
                  responseParameterElementString = '<responseparam type="equal"/>\n'
              else                            # else this is not the first answer
                if plusMinus and tolerance    # author has supplied a tolerance specification on the *first* answer
                  hintMatches = line.match( /{{(.+)}}/ )  # extract the {{...}} phrase, if any
                  if hintMatches
                    hintText = hintMatches[1].trim()
                    numericHintElementString += '<numerichint answer="' + answerExpression + '" tolerance="' + tolerance + '">' + hintText + '\n</numerichint>\n'
                else
                  responseParameterElementString = '<responseparam type="equal"/>\n'

      returnXmlString += MarkdownEditingDescriptor.insertParagraphText(xmlString, reducedXmlString)
      returnXmlString +=  '    <numericalresponse answer="' + answerString  + '">\n'
      returnXmlString += '        ' + responseParameterElementString
      returnXmlString += '        <formulaequationinput/>\n'
      returnXmlString += '        ' + correctHintElementString
      returnXmlString += '        ' + numericHintElementString
      returnXmlString +=  '    </numericalresponse>\n'
    else                        # else this is not a numeric problem
      returnXmlString = xmlString
    return returnXmlString



  @markdownToXml: (markdown)->
    toXml = `function (markdown) {
      var xml = markdown,
          i, splits, scriptFlag;

      // replace headers
      xml = xml.replace(/(^.*?$)(?=\n\=\=+$)/gm, '<h1>$1</h1>');
      xml = xml.replace(/\n^\=\=+$/gm, '');
      xml = xml + '\n';       // add a blank line at the end of the string (just belt and suspenders)

      xml = MarkdownEditingDescriptor.parseForProblemHints(xml);    // pull out any problem hints
      xml = MarkdownEditingDescriptor.parseForQuestionHints(xml);    // pull out any problem hints

 debugger;
 
      xml = MarkdownEditingDescriptor.parseForNumeric(xml);

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

            hintText = '';
            hintMatches = options[i].match( /_([0-9]+)_/ ); // check for an extracted hint string
            if(hintMatches) {                               // if we found one
              hintIndex = parseInt(hintMatches[1]);
              hintText = MarkdownEditingDescriptor.questionHintStrings[ hintIndex ];
              hintText = hintText.trim();
              hintText = MarkdownEditingDescriptor.extractCustomLabel( hintText );
              value = value.replace(hintMatches[0], '');  // remove the hint marker, else it will be displayed
            }

            choices += '    <choice correct="' + correct + '"' + fixed + '>' + value + '\n';
            if(hintText) {
              choices += '        <choicehint ' + MarkdownEditingDescriptor.customLabel + '>' + hintText + '\n'
              choices += '        </choicehint>\n'
            }
            choices += '    </choice>\n';
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

      //_____________________________________________________________________
      //
      // checkbox questions
      //
      xml = xml.replace(/(^\s+(\[[x ]+|_[0-9]+)[^\n]+\n)+/gm, function(match) {
        return MarkdownEditingDescriptor.parseForCheckbox(match);
      });

//      // replace string and numerical
//      xml = xml.replace(/(^\=\s*(.*?$)(\n*or\=\s*(.*?$))*)+/gm, function(match, p) {
//          // Split answers
//          debugger;
//          var answersList = p.replace(/^(or)?=[^\n]+/gm, '').split('\n'),
//
//              processNumericalResponse = function (value) {
//                  var params, answer, string;
//
//                  if (_.contains([ '[', '(' ], value[0]) && _.contains([ ']', ')' ], value[value.length-1]) ) {
//                    // [5, 7) or (5, 7), or (1.2345 * (2+3), 7*4 ]  - range tolerance case
//                    // = (5*2)*3 should not be used as range tolerance
//                    string = '<numericalresponse answer="' + value +  '">\n';
//                    string += '  <formulaequationinput />\n';
//                    string += '</numericalresponse>\n\n';
//                    return string;
//                  }
//
//                  if (isNaN(parseFloat(value))) {
//                      return false;
//                  }
//
//                  // Tries to extract parameters from string like 'expr +- tolerance'
//                  params = /(.*?)\+\-\s*(.*?$)/.exec(value);
//
//                  if(params) {
//                      answer = params[1].replace(/\s+/g, ''); // support inputs like 5*2 +- 10
//                      string = '<numericalresponse answer="' + answer + '">\n';
//                      string += '  <responseparam type="tolerance" default="' + params[2] + '" />\n';
//                  } else {
//                      answer = value.replace(/\s+/g, ''); // support inputs like 5*2
//                      string = '<numericalresponse answer="' + answer + '">\n';
//                  }
//
//                  string += '  <formulaequationinput />\n';
//                  string += '</numericalresponse>\n\n';
//
//                  return string;
//              },
//
//              processStringResponse = function (values) {
//                  var firstAnswer = values.shift(), string;
//
//                  if (firstAnswer[0] === '|') { // this is regexp case
//                      string = '<stringresponse answer="' + firstAnswer.slice(1).trim() +  '" type="ci regexp" >\n';
//                  } else {
//                      string = '<stringresponse answer="' + firstAnswer +  '" type="ci" >\n';
//                  }
//
//                  for (i = 0; i < values.length; i += 1) {
//                      string += '  <additional_answer>' + values[i] + '</additional_answer>\n';
//                  }
//
//                  string +=  '  <textline size="20"/>\n</stringresponse>\n\n';
//
//                  return string;
//              };
//
//          return processNumericalResponse(answersList[0]) || processStringResponse(answersList);
//      });

      //_____________________________________________________________________
      //
      // drop down questions
      //
      xml = xml.replace(/\[\[([^\]]+)\]\]/g, function(match, p) {
        return MarkdownEditingDescriptor.parseForDropdown(match);
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

      xml = MarkdownEditingDescriptor.insertProblemHints(xml);      // insert any extracted problem hints

      // make all elements descendants of a single problem element
      xml = '<problem schema="edXML/1.0">\n' + xml + '\n</problem>';

      return xml;
    }`
    return toXml markdown

