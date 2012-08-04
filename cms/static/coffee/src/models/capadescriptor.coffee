class @CapaWikiDescriptor
  constructor: (@element) ->
    @loadParser("/static/peg/capawiki.jspeg")
    @capaBox = $(".capa-box", @element)
    @wikiBox = $(".wiki-box", @element)

  save: ->
    {'capa': @capaBox.val(), 'wiki': @wikiBox.val()}

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

  serializeDomToCapaXML: (node) ->
    # serializes a Capa XML document and make changes if needed 
    # e.g. replace <text> into <startouttext />
    serializer = new XMLSerializer()
    capa = serializer.serializeToString(node)

  buildXML: (parsed) ->
    domParser = new DOMParser()
    doc = domParser.parseFromString("<problem />", "text/xml");
    problem = $(doc).find('problem')

    createTextElement = (content) ->
      el = $(doc.createElement('text'))
      for line in content.split('\n')
        el.append doc.createTextNode(line)
        el.append doc.createElement('br')
      el.children().last().remove()
      return el

    replaceVariableNameWrapper = (expression) ->
      match = /^\{(.+)\}$/.exec(expression)
      return if match then "$" + match[1] else expression

    for section in parsed
      if section.type == 'text'
        newel = createTextElement(section.text)
        problem.append(newel)

      else if section.type == 'image'
        center = $(doc.createElement('center'))
        img = $(doc.createElement('img'))
        img.attr 'src', section.url
        center.append img
        if section.title
          title = createTextElement(section.title)
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
          choice.append createTextElement(choice_def.text)
          group.append(choice)

        problem.append(newel)

      else if section.type == 'numerical'
        newel = $(doc.createElement('numericalresponse'))
        newel.attr 'answer', replaceVariableNameWrapper(section.answer)

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
        newel.attr 'answer', replaceVariableNameWrapper(section.answer)

        newel.append doc.createElement('textline') 
        problem.append(newel)

      else if section.type == 'formula'
        formularesponse = $(doc.createElement("formularesponse"))
        formularesponse.attr 'samples', section.samples
        formularesponse.attr 'answer', replaceVariableNameWrapper(section.answer)
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

    capa = @serializeDomToCapaXML(doc)
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
    