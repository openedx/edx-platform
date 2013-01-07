describe 'MarkdownEditingDescriptor', ->

  describe 'insertMultipleChoice', ->
    it 'inserts the template if selection is empty', ->
      revisedSelection = MarkdownEditingDescriptor.insertMultipleChoice('')
      expect(revisedSelection).toEqual(MarkdownEditingDescriptor.multipleChoiceTemplate)
    it 'wraps existing text', ->
      revisedSelection = MarkdownEditingDescriptor.insertMultipleChoice('foo\nbar')
      expect(revisedSelection).toEqual('( ) foo\n( ) bar\n')
    it 'recognizes x as a selection if there is non-whitespace after x', ->
      revisedSelection = MarkdownEditingDescriptor.insertMultipleChoice('a\nx b\nc\nx \nd\n x e')
      expect(revisedSelection).toEqual('( ) a\n(x) b\n( ) c\n( ) x \n( ) d\n(x) e\n')
    it 'removes multiple newlines', ->
      revisedSelection = MarkdownEditingDescriptor.insertMultipleChoice('a\nx b\n\n\nc')
      expect(revisedSelection).toEqual('( ) a\n(x) b\n( ) c\n')

  describe 'insertCheckboxChoice', ->
    # Note, shares code with insertMultipleChoice. Therefore only doing smoke test.
    it 'inserts the template if selection is empty', ->
      revisedSelection = MarkdownEditingDescriptor.insertCheckboxChoice('')
      expect(revisedSelection).toEqual(MarkdownEditingDescriptor.checkboxChoiceTemplate)
    it 'wraps existing text', ->
      revisedSelection = MarkdownEditingDescriptor.insertCheckboxChoice('foo\nbar')
      expect(revisedSelection).toEqual('[ ] foo\n[ ] bar\n')

  describe 'insertStringInput', ->
    it 'inserts the template if selection is empty', ->
      revisedSelection = MarkdownEditingDescriptor.insertStringInput('')
      expect(revisedSelection).toEqual(MarkdownEditingDescriptor.stringInputTemplate)
    it 'wraps existing text', ->
      revisedSelection = MarkdownEditingDescriptor.insertStringInput('my text')
      expect(revisedSelection).toEqual('= my text')

  describe 'insertNumberInput', ->
    it 'inserts the template if selection is empty', ->
      revisedSelection = MarkdownEditingDescriptor.insertNumberInput('')
      expect(revisedSelection).toEqual(MarkdownEditingDescriptor.numberInputTemplate)
    it 'wraps existing text', ->
      revisedSelection = MarkdownEditingDescriptor.insertNumberInput('my text')
      expect(revisedSelection).toEqual('= my text')

  describe 'insertSelect', ->
    it 'inserts the template if selection is empty', ->
      revisedSelection = MarkdownEditingDescriptor.insertSelect('')
      expect(revisedSelection).toEqual(MarkdownEditingDescriptor.selectTemplate)
    it 'wraps existing text', ->
      revisedSelection = MarkdownEditingDescriptor.insertSelect('my text')
      expect(revisedSelection).toEqual('[[my text]]')

  describe 'markdownToXml', ->
    it 'converts raw text to paragraph', ->
      data = MarkdownEditingDescriptor.markdownToXml('foo')
      expect(data).toEqual('<problem>\n<p>foo</p>\n</problem>')