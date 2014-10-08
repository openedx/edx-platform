# The function of this file is a bit confusing because:
#
#    - it is a ‘coffee’ file designed to produce javascript source files when
#      run through the coffee processor, and
#
#    - one of the primary functions performed by the code here is contained
#      in the function ‘markdownToXml’ at the very end of the file—which
#      Is just one large verbatim javascript function (notice the back tick
#      just before the ‘function (markdown) {‘)
#
# So, most of the code resulting from processing of this file will be javascript
# But the function is *already* essentially javascript which is simply passed
# through.
#
# The function ‘markdownToXml’ is responsible for the parsing and
# interpretation of a block of markdown text constructed by a course author
# in the simple editor. The function transforms the input string from ‘markdown’
# format to a hybrid XML/HTML format. The transformation is carried out in a
# series of steps with regex replacements doing most of the work.
#
# There is an important subtlety here: each replacement pattern is applied
# repeatedly to any substring of text which matches the search expression.
# For example, suppose the input string includes three questions: a multiple
# choice question, a text input question, another multiple choice question,
# and a drop down question:
#
# 	Multiple Choice Question (markdown)
# 	Text Input Question (markdown)
# 	Multiple Choice Question (markdown)
# 	Drop Down Question (markdown)
#
# The first regex replacement step looks for multiple choice questions in
# the string and in this example two will be found. Both those substrings
# will be transformed into XML/HTML resulting in a new string held in
# variable ‘xml’ which will be passed on to the next stage of the
# transformation process:
#
# 	Multiple Choice Question (XML/HTML)
# 	Text Input Question (markdown)
# 	Multiple Choice Question (XML/HTML)
# 	Drop Down Question (markdown)
#
# Next, a search pattern designed to find checkbox questions is applied but,
# in our example, nothing matches the pattern so no change is made to
# the ‘xml’ string.
#
# Now the process repeated with a numeric input question pattern, but
# none is found.
#
# A text input question pattern is applied and this time one question is
# found and transformed to XML/HTML:
#
# 	Multiple Choice Question (XML/HTML)
# 	Text Input Question (XML/HTML)
# 	Multiple Choice Question (XML/HTML)
# 	Drop Down Question (markdown)
#
# A drop down question pattern is applied and one question is found
# and transformed:
#
# 	Multiple Choice Question (XML/HTML)
# 	Text Input Question (XML/HTML)
# 	Multiple Choice Question (XML/HTML)
# 	Drop Down Question (XML/HTML)
#
# Finally, some miscellaneous cleanup is done, including wrapping
# the entire transformed string in a root element <problem>..</problem> pair of tags.
#

class @MarkdownEditingDescriptor extends XModule.Descriptor
  # TODO really, these templates should come from or also feed the cheatsheet
  @multipleChoiceTemplate : "( ) incorrect\n( ) incorrect\n(x) correct\n"
  @checkboxChoiceTemplate: "[x] correct\n[ ] incorrect\n[x] correct\n"
  @stringInputTemplate: "= answer\n"
  @numberInputTemplate: "= answer +- 0.001%\n"
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
  # check a hint string for a custom label (e.g., 'NOPE::you got this answer wrong')
  # if found, remove the label and the :: delimiter and save the label in the
  # 'customLabel' variable for later handling
  #
  @extractCustomLabel: (feedbackString) ->
    returnString = feedbackString  # assume we will find no custom label
    tokens = feedbackString.split('::')
    if tokens.length > 1  # check for a custom label to precede the feedback string
      @customLabel = ' label="' + tokens[0].trim() + '"'    # save the custom label for insertion into the XML
      returnString = tokens[1].trim()
    else
      @customLabel = ''
    return returnString  # return the feedback string but without the custom label, if any

  #________________________________________________________________________________
  # search for any text demarcated as a 'question hint' by the double braces {{..}}
  # if found, copy the text to an array for later insertion and remove that text
  # from the xmlString, replacing it with a unique marker for later restoration
  #
  @extractDistractorHints: (xmlString) ->
    @distractorHintStrings = []    # initialize the strings array

    DOUBLE_LEFT_BRACE_MARKER = '~~~'
    DOUBLE_RIGHT_BRACE_MARKER = '```'
    xmlString = xmlString.replace(/\{\{/g, DOUBLE_LEFT_BRACE_MARKER)   # replace all double left braces with '~~~~'
    xmlString = xmlString.replace(/}}/g, DOUBLE_RIGHT_BRACE_MARKER)    # replace all double right braces with '```'

    distractorHintMatches = xmlString.match(/~~~[^`]+```/gm)
    if distractorHintMatches
      index = 0
      for distractorHintMatch in distractorHintMatches
        xmlString = xmlString.replace( distractorHintMatch, '_' + index++ + '_')
        distractorHintMatch = distractorHintMatch.replace(/~~~/gm, '')
        distractorHintMatch = distractorHintMatch.replace(/```/gm, '')
        distractorHintMatch = distractorHintMatch.replace(/\n/gm, '_RETURN_')
        @distractorHintStrings.push(distractorHintMatch)   # save the string but no delimiters

    return xmlString

  #________________________________________________________________________________
  # search for any text demarcated as a 'problem hint' by the double vertical bars
  # if found, copy the text to an array for later insertion and remove that text
  # from the xmlString
  #
  @extractProblemHints: (xmlString) ->
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
  @restoreProblemHints: (xmlStringUnderConstruction) ->
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
  @parseForDropdown: (xmlString) ->
    # parse the supplied string knowing it is a drop down component

    correctAnswerText = ''
    correctAnswerFound = false
    dropdownMatches = xmlString.match( /\[\[([^\]]+)\]\]/ )   # try to match an opening and closing double bracket
    if dropdownMatches  # the xml has an opening and closing double bracket [[...]]
      returnXmlString +=  '\n<optionresponse>\n'
      returnXmlString += '    <optioninput options="OPTIONS_PLACEHOLDER" correct="CORRECT_PLACEHOLDER">\n'
      optionsString = ''
      delimiter = ''

      dropdownMatch = dropdownMatches[1]              # the match string is the entire set of drop down options

      for line in dropdownMatch.split( /[,\n]/)  # split the string between [[..]] brackets into single lines
        line = line.trim()
        if line.length > 0
          hintText = ''
          correctnessText = ''
          itemText = ''

          hintMatches = line.match( /_([0-9]+)_/ ); # check for an extracted hint string
          if hintMatches  # if we found one
            hintIndex = parseInt(hintMatches[1])
            hintText = MarkdownEditingDescriptor.distractorHintStrings[ hintIndex ]
            hintText = hintText.trim()
            hintText = MarkdownEditingDescriptor.extractCustomLabel( hintText )
            line = line.replace(hintMatches[0], '')  # remove the hint marker, else it will be displayed

          correctChoiceMatch = line.match( /^\s*\(([^)]+)\)/ )  # try to match a parenthetical string: '(...)'
          if correctChoiceMatch and not correctAnswerFound  # matched so this must be the correct answer
            correctnessText = 'True'
            itemText = correctChoiceMatch[1]
            correctAnswerText = itemText
            correctAnswerFound = true
            optionsString += delimiter + "(" + itemText.trim() + ")"
          else
            correctnessText = 'False'
            itemText = line.trim()
            optionsString += delimiter  + itemText.trim()

          if itemText[itemText.length-1] == ','     # check for an end-of-line comma
            itemText = itemText.slice(0, itemText.length-1) # suppress it

          returnXmlString += '          <option  correct="' + correctnessText + '">' + itemText.trim()
          if hintText
            returnXmlString += '\n'
            returnXmlString += '               <optionhint ' + @customLabel + '>' + hintText + '\n'
            returnXmlString += '               </optionhint>\n'
          returnXmlString += '          </option>\n'

          delimiter = ','
      returnXmlString += '    </optioninput>\n'
      returnXmlString = returnXmlString.replace('OPTIONS_PLACEHOLDER', optionsString)  # poke the options in
      returnXmlString += '</optionresponse>\n'
    else
      returnXmlString = xmlString

    returnXmlString = returnXmlString.replace('CORRECT_PLACEHOLDER', correctAnswerText)  # poke the correct value in

    return returnXmlString

  #________________________________________________________________________________
  @parseForCheckbox: (xmlString) ->
    # parse the supplied string knowing it is a checkbox component
    choiceString = ''
    reducedXmlString = ''
    booleanExpressionStrings = []
    booleanHintPhrases = []
    returnXmlString = xmlString

    for line in xmlString.split('\n')
      correctnessText = ''
      itemText = ''
      hintTextSelected = ''
      hintTextUnselected = ''

      choiceMatches = line.match(/(\s*\[\s*x?\s*\])([^\n]+)/)
      if choiceMatches  # this line includes '[...]' so it must be a checkbox choice
        line = choiceMatches[2]  # remove the [..] phrase, else it will be displayed to student
        hintMatches = line.match( /_([0-9]+)_/ )  # check for an extracted hint string
        if hintMatches
          line = line.replace(hintMatches[0], '')  # remove the {{...}} phrase, else it will be displayed to student

          hintIndex = parseInt(hintMatches[1])
          combinedHintText = MarkdownEditingDescriptor.distractorHintStrings[ hintIndex ]
          combinedHintText = combinedHintText.trim()
          combinedHintText = combinedHintText.replace( /(selected:|s:)/i, "S:")
          combinedHintText = combinedHintText.replace( /(unselected:|u:)/i, "U:")
          selectedMatches = combinedHintText.match(/\s*S:\s*([^}]+)/)
          unselectedMatches = combinedHintText.match(/\s*U:\s*([^}]+)/)

          if selectedMatches and unselectedMatches  # both a selected and unselected phrase were supplied for this choice
            hintTextSelected = selectedMatches[1]
            hintTextUnselected = unselectedMatches[1]

        correctnessText = 'false'
        if choiceMatches[1].match(/X/i)
          correctnessText = 'true'

        choiceString += '    <choice correct="' + correctnessText + '">' + line.trim()
        if hintTextSelected.length > 0 and hintTextUnselected.length > 0
          choiceString += '\n'
          choiceString += '               <choicehint selected="true">' + hintTextSelected + '\n'
          choiceString += '               </choicehint>\n'
          choiceString += '               <choicehint selected="false">' + hintTextUnselected + '\n'
          choiceString += '               </choicehint>\n    '
        choiceString += '</choice>\n'

      else  # this line is not a checkbox choice, but it may be a combination hint spec line
        hintMatches = line.match( /_([0-9]+)_/ )  # check for an extracted hint string
        if hintMatches  # the line does contain an extracted hint string
          returnXmlString = returnXmlString.replace(hintMatches[0], '')  # remove the phrase, else it will be displayed to student
          hintIndex = parseInt(hintMatches[1])
          hintText = MarkdownEditingDescriptor.distractorHintStrings[ hintIndex ]
          hintText = hintText.trim()
          combinationHintMatch = hintText.match( /\(\((.+)\)\)(.+)/ )
          if combinationHintMatch  # the line does contain a combination hint phrase
            booleanExpressionStrings.push(combinationHintMatch[1])
            booleanHintPhrases.push(combinationHintMatch[2])

    if choiceString
      returnXmlString =  '<choiceresponse>\n'
      returnXmlString += '  <checkboxgroup direction="vertical">\n'
      returnXmlString += choiceString
      index = 0
      for booleanExpression in booleanExpressionStrings
        booleanHintPhrase = booleanHintPhrases[index++]
        returnXmlString += '    <booleanhint value="' + booleanExpression + '">' + booleanHintPhrase + '\n'
        returnXmlString += '    </booleanhint>\n'
      returnXmlString += '  </checkboxgroup>\n'

      returnXmlString += '</choiceresponse>\n'

    return returnXmlString

    
  #________________________________________________________________________________
  @parseForNumeric: (xmlString) ->
    # parse the supplied string knowing it is a numeric component
    returnXmlString = xmlString
    operator = ''
    answerExpression = ''
    answerString = ''
    plusMinus = ''
    tolerance = ''
    responseParameterElementString = ''
    hintElementString = ''

    for line in xmlString.split('\n')
      numericMatch = line.match(/^\s*([or=!]+)\s*([ \d,\.\)([\]\-\%*/]+)\s*([\d,\.\)([\]+\-\%*/]*)\s*([\d,\.\)([\]+\-\%*/]*)/)
      if numericMatch
        if numericMatch[1]  # if an operator was found
          operator = numericMatch[1].trim()

        if numericMatch[2]  # if an answer expression may have been found
          answerExpression = numericMatch[2].trim()
          if answerExpression
            if numericMatch[3].trim() == '+-'  # if a plus/minus was found
              plusMinus = numericMatch[3].trim()
            else
              answerExpression += numericMatch[3].trim()  # add in the second half of the expression, if any

            if answerExpression.match(/(\[|\()/)  # if a leading '(' or '[' found
              rangeExpression = ''  # assume we won't find a range expression
              if answerExpression.match(/\((.*?)\)/) or answerExpression.match(/\[(.*?)\]/)  # if a range expression was found

                parenCheckMatch = answerExpression.match(/\((.*?,.*?)\)/)  # check for a (.. , ..) answer expression
                if parenCheckMatch != null
                  rangeExpression = parenCheckMatch[1]  # this is the expression contained by the parentheses

                bracketCheckMatch = answerExpression.match(/\[(.*?,.*?)\]/)  # check for a [.. , ..] answer expression
                if bracketCheckMatch != null
                  rangeExpression = bracketCheckMatch[1]  # this is the expression contained by the brackets

              if rangeExpression.length > 0  # if we found a range expression, we'll validate it
                if not rangeExpression.match(/[\.\s\d+\-\%*/,]+/) # if anything but whitespace and math is found
                  operator = ''  # obliterate the operator to ignore this line
              else  # we didn't find a valid range expression
                operator = ''  # obliterate the operator to ignore this line

            if numericMatch[4]  # if a tolerance value was detected
              tolerance = numericMatch[4].trim()

            if operator == '='
              if answerExpression
                hintMatches = line.match( /_([0-9]+)_/ )          # check for an extracted hint string
                if hintMatches  # the line does contain an extracted hint string
                  xmlString = xmlString.replace(hintMatches[0], '')  # remove the phrase, else it will be displayed
                  answerExpression = answerExpression.replace(hintMatches[0], '')
                  answerExpression = answerExpression.trim()
                  hintIndex = parseInt(hintMatches[1])
                  hintText = MarkdownEditingDescriptor.distractorHintStrings[ hintIndex ]
                  hintText = hintText.trim()
                  hintText = MarkdownEditingDescriptor.extractCustomLabel( hintText )

                if answerString == ''           # if this is the *first* answer supplied
                  answerString = answerExpression
                  if hintText
                    hintElementString = '<correcthint ' + @customLabel + '>' + hintText + '\n        </correcthint>\n'
                  if plusMinus and tolerance  # author has supplied a tolerance specification on the *first* answer
                    responseParameterElementString = '  <responseparam type="tolerance" default="' + tolerance + '" />\n'

            if operator == 'or='        # this is a weird case because we have to discard this answer--it isn't
                                        # yet supported in the code although it will be soon
              returnXmlString = returnXmlString.replace(line, '')     # just throw it away for now

    if answerString
      returnXmlString  = '<numericalresponse answer="' + answerString  + '">\n'
      returnXmlString += responseParameterElementString
      returnXmlString += '  <formulaequationinput />\n'
      returnXmlString += hintElementString
      returnXmlString += '</numericalresponse>'
    return returnXmlString

  #________________________________________________________________________________
  @parseForText: (xmlString) ->
    # parse the supplied string knowing it is a text input problem -- the markdown
    # associated with any numeric input questions (which look very similar to
    # text input questions from the parser's point of view) will have been extracted
    # before this point in processing
    returnXmlString = xmlString
    operator = ''
    answerExpression = ''
    additionalAnswerString = ''
    answerString = ''
    hintElementString = ''
    ciString = 'type="ci"'

    for line in xmlString.split('\n')
      textMatch = line.match( /^\s*(!?(not)?(or)?=)([^\n]+)/ )
      hintText = ''
      if textMatch
        if textMatch[1]
          operator = textMatch[1].trim()
        if textMatch[4]
          answerExpression = textMatch[4].trim()

        if operator == '=' or operator == 'or='
          if answerExpression
            hintMatches = line.match( /_([0-9]+)_/ ) # check for an extracted hint string
            if hintMatches  # the line does contain an extracted hint string
              xmlString = xmlString.replace(hintMatches[0], '')  # remove the phrase, else it will be displayed
              answerExpression = answerExpression.replace(hintMatches[0], '')
              answerExpression = answerExpression.trim()
              hintIndex = parseInt(hintMatches[1])
              hintText = MarkdownEditingDescriptor.distractorHintStrings[ hintIndex ]
              hintText = hintText.trim()
              hintText = MarkdownEditingDescriptor.extractCustomLabel( hintText )

            if answerString == ''           # if this is the *first* answer supplied
              answerString = answerExpression

              if answerString[0] == '|'      # if the first character is '|' the answer is a regex
                ciString = 'type="ci regexp"'
                answerString = answerString.replace('|', '').trim()

              if hintText
                hintElementString = '    <correcthint ' + @customLabel + '>' + hintText + '\n    </correcthint>\n'
            else
              if hintText
                hintElementString += '    <additional_answer  answer="' +
                  answerExpression + '">' + hintText + '\n  </additional_answer>\n'
              else
                additionalAnswerString += '  <additional_answer>' + answerExpression + '</additional_answer>\n'

    if answerString
      returnXmlString  =  '<stringresponse answer="' + answerString  + '" ' + ciString + ' >\n'
      returnXmlString += hintElementString
      returnXmlString += additionalAnswerString
      returnXmlString += '  <textline size="20"/>\n'
      returnXmlString +=  '</stringresponse>\n'
    return returnXmlString

  @markdownToXml: (markdown)->
    toXml = `function (markdown) {
      var xml = markdown,
          i, splits, scriptFlag;

      // replace headers
      xml = xml.replace(/(^.*?$)(?=\n\=\=+$)/gm, '<h1>$1</h1>\n');
      xml = xml.replace(/\n^\=\=+$/gm, '');
      xml = xml + '\n';       // add a blank line at the end of the string (just belt and suspenders)
      xml = MarkdownEditingDescriptor.extractProblemHints(xml);    // pull out any problem hints
      xml = MarkdownEditingDescriptor.extractDistractorHints(xml);    // pull out any problem hints

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
              hintText = MarkdownEditingDescriptor.distractorHintStrings[ hintIndex ];
              hintText = hintText.trim();
              hintText = MarkdownEditingDescriptor.extractCustomLabel( hintText );
              value = value.replace(hintMatches[0], '');  // remove the hint marker, else it will be displayed
            }

            choices += '    <choice correct="' + correct + '"' + fixed + '>' + value;
            if(hintText) {
              choices += '\n';
              choices += '        <choicehint' + MarkdownEditingDescriptor.customLabel + '>' + hintText + '\n';
              choices += '        </choicehint>\n    ';
            }
            choices += '</choice>\n';
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
        result += '</multiplechoiceresponse>\n';
        return result;
      });

      //_____________________________________________________________________
      //
      // checkbox questions
      //
      xml = xml.replace(/(^\s*(\[.*]|[0-9_]+)\s*[^\n]+\n)+/gm, function(match) {
        return MarkdownEditingDescriptor.parseForCheckbox(match);
      });

      //_____________________________________________________________________
      //
      // numeric input questions
      //
      xml = xml.replace( /(^\s*(or)?=[^\n]+)+/gm, function(match) {
        return MarkdownEditingDescriptor.parseForNumeric(match);
      });

      //_____________________________________________________________________
      //
      // text input questions
      //
      xml = xml.replace( /(^\s*(or)?=[^\n]+\n)+/gm, function(match) {
        return MarkdownEditingDescriptor.parseForText(match);
      });

      //_____________________________________________________________________
      //
      // drop down questions
      //
      xml = xml.replace(/(\s*\[\[[^\]]+]])+/g, function(match, p) {
        return MarkdownEditingDescriptor.parseForDropdown(match);
      });

      // replace explanations
      xml = xml.replace(/\[explanation\]\n?([^\]]*)\[\/?explanation\]/gmi, function(match, p1) {
         var selectString = '\n<solution>\n<div class="detailed-solution">\nExplanation\n\n' + p1 + '\n</div>\n</solution>';

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
              splits[i] = splits[i].replace(/^\s*((?!\s*\<|$).*$)/gm, '<p>$1</p>');
          }

          if(/\<\/(script|pre)/.test(splits[i])) {
              scriptFlag = false;
          }
      }

      xml = xml.replace(/(<p>\s*<\/p>)/gm, '');      // remove empty paragraph tags

      xml = splits.join('');

      xml = xml.replace(/_RETURN_/gm, '\n');         // replace any RETURN markers with the original '\n' character

      // remove superfluous lines
      xml = xml.replace(/\n\n\n/g, '\n');

      xml = MarkdownEditingDescriptor.restoreProblemHints(xml);      // insert any extracted problem hints

      // make all elements descendants of a single problem element
      xml = '<problem>\n' + xml + '</problem>';

      return xml;
    }`
    return toXml markdown

