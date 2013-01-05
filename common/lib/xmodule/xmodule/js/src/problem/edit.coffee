class @MarkdownEditingDescriptor extends XModule.Descriptor
  constructor: (element) ->
    $body.on('click', '.editor-tabs .tab', @changeEditor)

    @xml_editor = CodeMirror.fromTextArea($(".xml-box", element)[0], {
    mode: "xml"
    lineNumbers: true
    lineWrapping: true
    })
    @current_editor = @xml_editor

    if $(".markdown-box", element).length != 0
      @markdown_editor = CodeMirror.fromTextArea($(".markdown-box", element)[0], {
      lineWrapping: true
      mode: null
      onChange: @onMarkdownEditorUpdate
      })
      @setCurrentEditor(@markdown_editor)

  onMarkdownEditorUpdate: ->
    console.log('update')
    @updateXML()

  updateXML: ->

  changeEditor: (e) =>
    e.preventDefault();
    $('.editor-tabs .current').removeClass('current')
    $(e.currentTarget).addClass('current')
    if (@current_editor == @xml_editor)
      @setCurrentEditor(@markdown_editor)
      #    onMarkdownEditorUpdate();
    else
      @setCurrentEditor(@xml_editor)
  #    xmlEditor.refresh();

  setCurrentEditor: (editor) ->
    $(@current_editor.getWrapperElement()).hide()
    @current_editor = editor
    $(@current_editor.getWrapperElement()).show()
    $(@current_editor).focus();

  save: ->
    $body.off('click', '.editor-tabs .tab', @changeEditor)
    data: @xml_editor.getValue()

  @markdownToXml: (markdown)->
    toXml = `function(markdown) {
      var xml = markdown;

      // replace headers
      xml = xml.replace(/(^.*?$)(?=\n\=\=+$)/gm, '<h1>$1</h1>');
      xml = xml.replace(/\n^\=\=+$/gm, '');

      // group multiple choice answers
      xml = xml.replace(/(^\s*\(.?\).*?$\n*)+/gm, function(match, p) {
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
        var groupString = '<multiplechoiceresponse>\n';
        groupString += '  <choicegroup type="MultipleChoiceChecks">\n';
        var options = match.split('\n');
        for(var i = 0; i < options.length; i++) {
          if(options[i].length > 0) {
            var value = options[i].split(/^\s*\[.?\]\s*/)[1];
            var correct = /^\s*\[x\]/i.test(options[i]);
            groupString += '    <choice correct="' + correct + '">' + value + '</choice>\n';
          }
        }
        groupString += '  </choicegroup>\n';
        groupString += '</multiplechoiceresponse>\n\n';
        return groupString;
      });

      // replace videos
      xml = xml.replace(/\{\{video\s(.*?)\}\}/g, '<video youtube="1.0:$1" />\n\n');

      // replace string and numerical
      xml = xml.replace(/^\=\s*(.*?$)/gm, function(match, p) {
        var string;
        var params = /(.*?)\+\-\s*(.*?)/.exec(p);
        if(parseFloat(p)) {
          if(params) {
            string = '<numericalresponse answer="' + params[1] + '">\n';
            string += '  <responseparam type="tolerance" default="' + params[2] + '" />\n';
          } else {
            string = '<numericalresponse answer="' + p + '">\n';
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
          selectString += "'" + options[i].replace(/\((.*?)\)/g, '$1') + "'" + (i < options.length -1 ? ',' : '');
        }
        selectString += ')" correct="';
        var correct = /\((.*?)\)/g.exec(p);
        if (correct) selectString += correct[1];
        selectString += '"></optioninput>\n';
        selectString += '</optionresponse>\n\n';
        return selectString;
      });

      // split scripts and wrap paragraphs
      var splits = xml.split(/(\<\/?script.*?\>)/g);
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

      return xml;
    }
    `
    return toXml markdown

