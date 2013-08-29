describe 'OpenEndedMarkdownEditingDescriptor', ->
  describe 'save stores the correct data', ->
    it 'saves markdown from markdown editor', ->
      loadFixtures 'combinedopenended-with-markdown.html'
      @descriptor = new OpenEndedMarkdownEditingDescriptor($('.combinedopenended-editor'))
      saveResult = @descriptor.save()
      expect(saveResult.metadata.markdown).toEqual('markdown')
      expect(saveResult.data).toEqual('<combinedopenended>\nmarkdown\n</combinedopenended>')
    it 'clears markdown when xml editor is selected', ->
      loadFixtures 'combinedopenended-with-markdown.html'
      @descriptor = new OpenEndedMarkdownEditingDescriptor($('.combinedopenended-editor'))
      @descriptor.createXMLEditor('replace with markdown')
      saveResult = @descriptor.save()
      expect(saveResult.nullout).toEqual(['markdown'])
      expect(saveResult.data).toEqual('replace with markdown')
    it 'saves xml from the xml editor', ->
      loadFixtures 'combinedopenended-without-markdown.html'
      @descriptor = new OpenEndedMarkdownEditingDescriptor($('.combinedopenended-editor'))
      saveResult = @descriptor.save()
      expect(saveResult.nullout).toEqual(['markdown'])
      expect(saveResult.data).toEqual('xml only')

  describe 'insertPrompt', ->
    it 'inserts the template if selection is empty', ->
      revisedSelection = OpenEndedMarkdownEditingDescriptor.insertPrompt('')
      expect(revisedSelection).toEqual(OpenEndedMarkdownEditingDescriptor.promptTemplate)
    it 'recognizes html in the prompt', ->
      revisedSelection = OpenEndedMarkdownEditingDescriptor.insertPrompt('[prompt]<h1>Hello</h1>[prompt]')
      expect(revisedSelection).toEqual('[prompt]<h1>Hello</h1>[prompt]')

  describe 'insertRubric', ->
    it 'inserts the template if selection is empty', ->
      revisedSelection = OpenEndedMarkdownEditingDescriptor.insertRubric('')
      expect(revisedSelection).toEqual(OpenEndedMarkdownEditingDescriptor.rubricTemplate)
    it 'recognizes a proper rubric', ->
      revisedSelection = OpenEndedMarkdownEditingDescriptor.insertRubric('[rubric]\n+1\n-1\n-2\n[rubric]')
      expect(revisedSelection).toEqual('[rubric]\n+1\n-1\n-2\n[rubric]')

  describe 'insertTasks', ->
    it 'inserts the template if selection is empty', ->
      revisedSelection = OpenEndedMarkdownEditingDescriptor.insertTasks('')
      expect(revisedSelection).toEqual(OpenEndedMarkdownEditingDescriptor.tasksTemplate)
    it 'recognizes a proper task string', ->
      revisedSelection = OpenEndedMarkdownEditingDescriptor.insertTasks('[tasks](Self)[tasks]')
      expect(revisedSelection).toEqual('[tasks](Self)[tasks]')

  describe 'markdownToXml', ->
    # test default templates
    it 'converts prompt to xml', ->
      data = OpenEndedMarkdownEditingDescriptor.markdownToXml("""[prompt]
                                                     <h1>Prompt!</h1>
                                                     This is my super awesome prompt.
                                                     [prompt]
                                                     """)
      data = data.replace(/[\t\n\s]/gmi,'')
      expect(data).toEqual("""
                           <combinedopenended>
                              <prompt>
                              <h1>Prompt!</h1>
                              This is my super awesome prompt.
                              </prompt>
                           </combinedopenended>
                           """.replace(/[\t\n\s]/gmi,''))

    it 'converts rubric to xml', ->
      data = OpenEndedMarkdownEditingDescriptor.markdownToXml("""[rubric]
                                                              + 1
                                                              -1
                                                              -2
                                                              + 2
                                                              -1
                                                              -2
                                                              +3
                                                              -1
                                                              -2
                                                              -3
                                                              [rubric]
                                                              """)
      data = data.replace(/[\t\n\s]/gmi,'')
      expect(data).toEqual("""
                           <combinedopenended>
                           <rubric>
                             <rubric>
                             <category>
                             <description>1</description>
                             <option>1</option>
                             <option>2</option>
                             </category>
                             <category>
                             <description>2</description>
                             <option>1</option>
                             <option>2</option>
                             </category>
                             <category>
                             <description>3</description>
                             <option>1</option>
                             <option>2</option>
                             <option>3</option>
                             </category>
                             </rubric>
                           </rubric>
                           </combinedopenended>
                           """.replace(/[\t\n\s]/gmi,''))

    it 'converts tasks to xml', ->
      data = OpenEndedMarkdownEditingDescriptor.markdownToXml("""[tasks]
                                                              (Self), ({1-2}AI), ({1-4}AI), ({1-2}Peer
                                                              [tasks]
                                                              """)
      data = data.replace(/[\t\n\s]/gmi,'')
      equality_list = """
                      <combinedopenended>
                        <task>
                        <selfassessment/>
                        </task>
                        <task>
                          <openended min_score_to_attempt="1" max_score_to_attempt="2">ml_grading.conf</openended>
                        </task>
                        <task>
                          <openended min_score_to_attempt="1" max_score_to_attempt="4">ml_grading.conf</openended>
                        </task>
                        <task>
                          <openended min_score_to_attempt="1" max_score_to_attempt="2">peer_grading.conf</openended>
                        </task>
                      </combinedopenended>
                      """
      expect(data).toEqual(equality_list.replace(/[\t\n\s]/gmi,''))
