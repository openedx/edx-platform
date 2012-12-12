describe 'HTMLEditingDescriptor', ->
  describe 'Read data from server, create Editor, and get data back out', ->
    it 'Does not munge &lt', ->
#     This is a test for Lighthouse #22,
#     "html names are automatically converted to the symbols they describe"
#     A better test would be a Selenium test to avoid duplicating the
#     mako template structure in html-edit-formattingbug.html.
#     However, we currently have no working Selenium tests.
      loadFixtures 'html-edit-formattingbug.html'
      @descriptor = new HTMLEditingDescriptor($('.html-edit'))
      data = @descriptor.save().data
      expect(data).toEqual("""&lt;problem&gt;
                              &lt;p&gt;&lt;/p&gt;
                              &lt;multiplechoiceresponse&gt;
                              <pre>&lt;problem&gt;
                                  &lt;p&gt;&lt;/p&gt;</pre>
                              <div><foo>bar</foo></div>""")