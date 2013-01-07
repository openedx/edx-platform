describe 'MarkdownEditingDescriptor', ->
  describe 'markdownToXml', ->
    it 'converts raw text to paragraph', ->
      data = MarkdownEditingDescriptor.markdownToXml('foo')
      expect(data).toEqual('<problem>\n<p>foo</p>\n</problem>')