class @OpenEndedMarkdownEditingDescriptor extends XModule.Descriptor
  # TODO really, these templates should come from or also feed the cheatsheet
  @rubricTemplate : """
                    [rubric]
                    + Ideas
                    - Difficult for the reader to discern the main idea.  Too brief or too repetitive to establish or maintain a focus.
                    - Attempts a main idea.  Sometimes loses focus or ineffectively displays focus.
                    - Presents a unifying theme or main idea, but may include minor tangents.  Stays somewhat focused on topic and task.
                    - Presents a unifying theme or main idea without going off on tangents.  Stays completely focused on topic and task.
                    + Content
                    - Includes little information with few or no details or unrelated details.  Unsuccessful in attempts to explore any facets of the topic.
                    - Includes little information and few or no details.  Explores only one or two facets of the topic.
                    - Includes sufficient information and supporting details. (Details may not be fully developed; ideas may be listed.)  Explores some facets of the topic.
                    - Includes in-depth information and exceptional supporting details that are fully developed.  Explores all facets of the topic.
                    + Organization
                    - Ideas organized illogically, transitions weak, and response difficult to follow.
                    - Attempts to logically organize ideas.  Attempts to progress in an order that enhances meaning, and demonstrates use of transitions.
                    - Ideas organized logically.  Progresses in an order that enhances meaning.  Includes smooth transitions.
                    + Style
                    - Contains limited vocabulary, with many words used incorrectly.  Demonstrates problems with sentence patterns.
                    - Contains basic vocabulary, with words that are predictable and common.  Contains mostly simple sentences (although there may be an attempt at more varied sentence patterns).
                    - Includes vocabulary to make explanations detailed and precise.  Includes varied sentence patterns, including complex sentences.
                    + Voice
                    - Demonstrates language and tone that may be inappropriate to task and reader.
                    - Demonstrates an attempt to adjust language and tone to task and reader.
                    - Demonstrates effective adjustment of language and tone to task and reader.
                    [rubric]
                    """

  @tasksTemplate: "[tasks]\n(Self), ({4-12}AI), ({9-12}Peer)\n[tasks]\n"
  @promptTemplate: """
                  [prompt]\n
                  <h3>Censorship in the Libraries</h3>

                  <p>'All of us can think of a book that we hope none of our children or any other children have taken off the shelf. But if I have the right to remove that book from the shelf -- that work I abhor -- then you also have exactly the same right and so does everyone else. And then we have no books left on the shelf for any of us.' --Katherine Paterson, Author
                  </p>

                  <p>
Write a persuasive essay to a newspaper reflecting your vies on censorship in libraries. Do you believe that certain materials, such as books, music, movies, magazines, etc., should be removed from the shelves if they are found offensive? Support your position with convincing arguments from your own experience, observations, and/or reading.
                  </p>
                  [prompt]\n
                   """

  constructor: (element) ->
    @element = element

    if $(".markdown-box", @element).length != 0
      @markdown_editor = CodeMirror.fromTextArea($(".markdown-box", element)[0], {
      lineWrapping: true
      mode: null
      })
      @setCurrentEditor(@markdown_editor)
      selection = @markdown_editor.getSelection()
      #Auto-add in the needed template if it isn't already in there.
      if(@markdown_editor.getValue() == "")
        @markdown_editor.setValue(OpenEndedMarkdownEditingDescriptor.promptTemplate + "\n" + OpenEndedMarkdownEditingDescriptor.rubricTemplate + "\n" + OpenEndedMarkdownEditingDescriptor.tasksTemplate)
      # Add listeners for toolbar buttons (only present for markdown editor)
      @element.on('click', '.xml-tab', @onShowXMLButton)
      @element.on('click', '.format-buttons a', @onToolbarButton)
      @element.on('click', '.cheatsheet-toggle', @toggleCheatsheet)
      # Hide the XML text area
      $(@element.find('.xml-box')).hide()
    else
      @createXMLEditor()

    @alertTaskRubricModification()

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

  alertTaskRubricModification: ->
    return alert("Before you edit, please note that if you alter the tasks block or the rubric block of this question after students have submitted responses, it may result in their responses and grades being deleted!  Use caution when altering problems that have already been released to students.")
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
    if !$(@markdown_editor.getWrapperElement()).find('.simple-editor-open-ended-cheatsheet')[0]
      @cheatsheet = $($('#simple-editor-open-ended-cheatsheet').html())
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
      data: OpenEndedMarkdownEditingDescriptor.markdownToXml(@markdown_editor.getValue())
      metadata:
        markdown: @markdown_editor.getValue()
      }
    else
      {
      data: @xml_editor.getValue()
      nullout: ['markdown']
      }

  @insertRubric: (selectedText) ->
    return OpenEndedMarkdownEditingDescriptor.insertGenericInput(selectedText, '[rubric]', '[rubric]', OpenEndedMarkdownEditingDescriptor.rubricTemplate)

  @insertPrompt: (selectedText) ->
    return OpenEndedMarkdownEditingDescriptor.insertGenericInput(selectedText, '[prompt]', '[prompt]', OpenEndedMarkdownEditingDescriptor.promptTemplate)

  @insertTasks: (selectedText) ->
    return OpenEndedMarkdownEditingDescriptor.insertGenericInput(selectedText, '[tasks]', '[tasks]', OpenEndedMarkdownEditingDescriptor.tasksTemplate)

  @insertGenericInput: (selectedText, lineStart, lineEnd, template) ->
    if selectedText.length > 0
      new_string = selectedText.replace(/^\s+|\s+$/g,'')
      if new_string.substring(0,lineStart.length) != lineStart
        new_string = lineStart + new_string
      if new_string.substring((new_string.length)-lineEnd.length,new_string.length) != lineEnd
        new_string = new_string + lineEnd
      return new_string
    else
      return template

  @markdownToXml: (markdown)->
    toXml = `function(markdown) {

      function template(template_html,data){
        return template_html.replace(/%(\w*)%/g,function(m,key){return data.hasOwnProperty(key)?data[key]:"";});
      }

      var xml = markdown;

      // group rubrics
      xml = xml.replace(/\[rubric\]\n?([^\]]*)\[\/?rubric\]/gmi, function(match, p) {
        var groupString = '<rubric>\n<rubric>\n';
        var options = p.split('\n');
        var category_open = false;
        for(var i = 0; i < options.length; i++) {
          if(options[i].length > 0) {
            var value = options[i].replace(/^\s+|\s+$/g,'');
            if (value.charAt(0)=="+") {
              if(i>0){
                if(category_open==true){
                  groupString += "</category>\n";
                  category_open = false;
                }
              }
              groupString += "<category>\n<description>\n";
              category_open = true;
              text = value.substr(1);
              text = text.replace(/^\s+|\s+$/g,'');
              groupString += text;
              groupString += "\n</description>\n";
            } else if (value.charAt(0) == "-") {
              groupString += "<option>\n";
              text = value.substr(1);
              text = text.replace(/^\s+|\s+$/g,'');
              groupString += text;
              groupString += "\n</option>\n";
            }
          }
          if(i==options.length-1 && category_open == true){
            groupString += "\n</category>\n";
          }
        }
        groupString += '</rubric>\n</rubric>\n';
        return groupString;
      });

      // group tasks
      xml = xml.replace(/\[tasks\]\n?([^\]]*)\[\/?tasks\]/gmi, function(match, p) {
        var open_ended_template = $('#open-ended-template').html();
        if(open_ended_template == null) {
          open_ended_template = "<openended %min_max_string%>%grading_config%</openended>";
        }
        var groupString = '';
        var options = p.split(",");
        for(var i = 0; i < options.length; i++) {
          if(options[i].length > 0) {
            var value = options[i].replace(/^\s+|\s+$/g,'');
            var lower_option = value.toLowerCase();
            type = lower_option.match(/(peer|self|ai)/gmi)
            if(type != null) {
              type = type[0]
              var min_max = value.match(/\{\n?([^\]]*)\}/gmi);
              var min_max_string = "";
              if(min_max!=null) {
                min_max = min_max[0].replace(/^{|}/gmi,'');
                min_max = min_max.split("-");
                min = min_max[0];
                max = min_max[1];
                min_max_string = 'min_score_to_attempt="' + min + '" max_score_to_attempt="' + max + '" ';
              }
              groupString += "<task>\n"
              if(type=="self") {
                groupString +="<selfassessment" + min_max_string + "/>"
              } else if (type=="peer") {
                config = "peer_grading.conf"
                groupString += template(open_ended_template,{min_max_string: min_max_string, grading_config: config});
              } else if (type=="ai") {
                                       config = "ml_grading.conf"
                                       groupString += template(open_ended_template,{min_max_string: min_max_string, grading_config: config});
              }
              groupString += "</task>\n"
            }
          }
        }
        return groupString;
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
