class @CapawikiDescriptor
  constructor: (@element) ->
    @loadParser("/static/peg/capawiki.jspeg")
    @capa_box = $(".capa-box", @element)
    @wiki_box = $(".wiki-box", @element)

  save: ->
    {'capa': @capa_box.val(), 'wiki': @wiki_box.val()}

  debug: (msg) ->
    # console.log msg

  loadParser: (url) ->
    @debug "Retrieving grammar rules from " + url
    $.get url, (data) =>
      @grammar = data
      @parser = PEG.buildParser @grammar
      @debug "Succuessfully built parser."
    , "text"

  buildParserErrorMessage: (e) ->
    if e.line != undefined && e.column != undefined
      "Line " + e.line + ", column " + e.column + ": " + e.message
    else e.message

  dom2capa: (node) ->
    serializer = new XMLSerializer()
    capa = serializer.serializeToString(node)

  buildXML: (parsed) ->
    dom_parser = new DOMParser()
    doc = dom_parser.parseFromString("<problem />", "text/xml");
    problem = $(doc).find('problem')

    create_text_element = (content) ->
      el = $(doc.createElement('text'))
      for line in content.split('\n')
        el.append doc.createTextNode(line)
        el.append doc.createElement('br')
      el.children().last().remove()
      return el

    variable_name_wrapper = (expression) ->
      match = /^\{(.+)\}$/.exec(expression)
      return if match then "$" + match[1] else expression

    for section in parsed
      if section.type == 'text'
        newel = create_text_element(section.text)
        problem.append(newel)

      else if section.type == 'image'
        center = $(doc.createElement('center'))
        img = $(doc.createElement('img'))
        img.attr 'src', section.url
        center.append img
        if section.title
          title = create_text_element(section.title)
          center.append doc.createElement('br')
          center.append title
        problem.append center

      else if section.type == 'multiple_choice'
        newel = $(doc.createElement('choiceresponse'))

        # count the number of correct choices
        num_correct = 0
        for choice in section.choices
          if choice.correct
            num_correct += 1 

        if num_correct == 1
          group = $(doc.createElement('radiogroup'))
        else if num_correct > 1
          group = $(doc.createElement('checkboxgroup'))
        newel.append(group)

        for choice_def in section.choices
          choice = $(doc.createElement('choice'))
          choice.attr 'correct', choice_def.correct
          choice.append create_text_element(choice_def.text)
          group.append(choice)

        problem.append(newel)

      else if section.type == 'numerical'
        newel = $(doc.createElement('numericalresponse'))
        newel.attr 'answer', variable_name_wrapper(section.answer)

        tolerance = $(doc.createElement('responseparam'))
        tolerance.attr 'type', 'tolerance'
        if section.tolerance == undefined
          section.tolerance = "5%"
        tolerance.attr 'default', section.tolerance
        tolerance.attr 'name', 'tol'
        tolerance.attr 'description', 'Numerical Tolerance'
        newel.append tolerance
        newel.append doc.createElement('textline') 
        problem.append(newel)

      else if section.type == 'string'
        newel = $(doc.createElement('stringresponse'))
        newel.attr 'answer', variable_name_wrapper(section.answer)

        newel.append doc.createElement('textline') 
        problem.append(newel)

      else if section.type == 'formula'
        formularesponse = $(doc.createElement("formularesponse"))
        formularesponse.attr 'samples', section.samples
        formularesponse.attr 'answer', variable_name_wrapper(section.answer)
        formularesponse.attr 'type', 'cs'

        tolerance = $(doc.createElement('responseparam'))
        tolerance.attr 'type', 'tolerance'
        if section.tolerance == undefined
          section.tolerance = "5%"
        tolerance.attr 'default', section.tolerance
        tolerance.attr 'name', 'tol'
        tolerance.attr 'description', 'Numerical Tolerance'

        formularesponse.append tolerance
        formularesponse.append doc.createElement('textline')
        problem.append(formularesponse)

      else
        throw new SyntaxError("unexpected section type " + section.type) 

    capa = @dom2capa(doc)
    return capa

  parse: (source) ->
    try
      result = @parser.parse (source + '\n')
      return {'result': result, 'status': 'success'}
    catch e
      message = @buildParserErrorMessage e
      return {'message': message, 'status': 'error'}

  convert: (parsed) ->
    try
      xml = @buildXML parsed
      return {'xml': xml, 'status': 'success'}
    catch e
      message = @buildParserErrorMessage e
      return {'message': message, 'status': 'error'}
    return done(xml)
    