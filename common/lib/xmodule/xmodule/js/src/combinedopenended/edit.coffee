class @OpenEndedMarkdownEditingDescriptor extends XModule.Descriptor
  # TODO really, these templates should come from or also feed the cheatsheet
  @rubricTemplate : "[rubric]\n+ Color Identification\n- Incorrect\n- Correct\n + Grammar\n- Poor\n- Acceptable\n- Superb \n[rubric]\n"
  @tasksTemplate: "[tasks]\n(Self), ({0,1}AI), ({1,3}Peer)\n[tasks]\n"
  @promptTemplate: "[prompt]\nWhy is the sky blue?\n[prompt]\n"

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
    if @confirmConversionToXml()
      @createXMLEditor(OpenEndedMarkdownEditingDescriptor.markdownToXml(@markdown_editor.getValue()))
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
      when "rubric-button" then revisedSelection = OpenEndedMarkdownEditingDescriptor.insertRubric(selection)
      when "prompt-button" then revisedSelection = OpenEndedMarkdownEditingDescriptor.insertPrompt(selection)
      when "tasks-button" then revisedSelection = OpenEndedMarkdownEditingDescriptor.insertTasks(selection)
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

    setTimeout (=> @cheatsheet.toggleClass('shown')), 10

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
      metadata:
        markdown: null
      }

  @insertRubric: (selectedText) ->
    return OpenEndedMarkdownEditingDescriptor.insertGenericInput(selectedText, '[rubric]', '[rubric]', OpenEndedMarkdownEditingDescriptor.rubricTemplate)

  @insertPrompt: (selectedText) ->
    return OpenEndedMarkdownEditingDescriptor.insertGenericInput(selectedText, '[prompt]', '[prompt]', OpenEndedMarkdownEditingDescriptor.promptTemplate)

  @insertTasks: (selectedText) ->
    return OpenEndedMarkdownEditingDescriptor.insertGenericInput(selectedText, '[tasks]', '[tasks]', OpenEndedMarkdownEditingDescriptor.tasksTemplate)

  @insertGenericInput: (selectedText, lineStart, lineEnd, template) ->
    if selectedText.length > 0
      # TODO: should this insert a newline afterwards?
      return lineStart + selectedText + lineEnd
    else
      return template

  @markdownToXml: (markdown)->
    toXml = `function(markdown) {
      var xml = markdown;

      // group rubrics
      xml = xml.replace(/\[rubric\]\n?([^\]]*)\[\/?rubric\]/gmi, function(match, p) {
        var groupString = '<multiplechoiceresponse>\n';
        groupString += '  <choicegroup type="MultipleChoice">\n';
        var options = match.split('\n');
        for(var i = 0; i < options.length; i++) {
          if(options[i].length > 0) {
            var value = options[i].split(/^\s*\(.?\)\s*/)[1];
            var correct = /^\s*\(x\)/i.test(options[i]);
            groupString += '    <choice correct="' + correct + '">' + value + '</choice>\n';
          }
        }
        groupString += '  </choicegroup>\n';
        groupString += '</multiplechoiceresponse>\n\n';
        return groupString;
      });

      // group check answers
      xml = xml.replace(/(^\s*\[.?\].*?$\n*)+/gm, function(match, p) {
        var groupString = '<choiceresponse>\n';
        groupString += '  <checkboxgroup direction="vertical">\n';
        var options = match.split('\n');
        for(var i = 0; i < options.length; i++) {
          if(options[i].length > 0) {
            var value = options[i].split(/^\s*\[.?\]\s*/)[1];
            var correct = /^\s*\[x\]/i.test(options[i]);
            groupString += '    <choice correct="' + correct + '">' + value + '</choice>\n';
          }
        }
        groupString += '  </checkboxgroup>\n';
        groupString += '</choiceresponse>\n\n';
        return groupString;
      });

      // replace string and numerical
      xml = xml.replace(/^\=\s*(.*?$)/gm, function(match, p) {
        var string;
        var floatValue = parseFloat(p);
        if(!isNaN(floatValue)) {
          var params = /(.*?)\+\-\s*(.*?$)/.exec(p);
          if(params) {
            string = '<numericalresponse answer="' + floatValue + '">\n';
            string += '  <responseparam type="tolerance" default="' + params[2] + '" />\n';
          } else {
            string = '<numericalresponse answer="' + floatValue + '">\n';
          }
          string += '  <textline />\n';
          string += '</numericalresponse>\n\n';
        } else {
          string = '<stringresponse answer="' + p + '" type="ci">\n  <textline size="20"/>\n</stringresponse>\n\n';
        }
        return string;
      });

      // replace selects
      xml = xml.replace(/\[\[(.+?)\]\]/g, function(match, p) {
        var selectString = '\n<optionresponse>\n';
        selectString += '  <optioninput options="(';
        var options = p.split(/\,\s*/g);
        for(var i = 0; i < options.length; i++) {
          selectString += "'" + options[i].replace(/(?:^|,)\s*\((.*?)\)\s*(?:$|,)/g, '$1') + "'" + (i < options.length -1 ? ',' : '');
        }
        selectString += ')" correct="';
        var correct = /(?:^|,)\s*\((.*?)\)\s*(?:$|,)/g.exec(p);
        if (correct) selectString += correct[1];
        selectString += '"></optioninput>\n';
        selectString += '</optionresponse>\n\n';
        return selectString;
      });

      // replace prompts
      xml = xml.replace(/\[prompt\]\n?([^\]]*)\[\/?prompt\]/gmi, function(match, p1) {
          var selectString = '<prompt>\n' + p1 + '\n</prompt>';
          return selectString;
      });

      // rid white space
      xml = xml.replace(/\n\n\n/g, '\n');

      // surround w/ combinedopenended tag
      xml = '<combinedopenended>\n' + xml + '\n</combinedopenended>';

      return xml;
    }
    `
    return toXml markdown