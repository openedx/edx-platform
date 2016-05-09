describe 'MarkdownEditingDescriptor', ->
  beforeEach ->
      jasmine.addMatchers
        toXMLEqual: ->
          return {
            compare: (actual, expected) ->
              {
                  pass: actual.replace(/\s+/g, '') == expected.replace(/\s+/g, '')
              }
          }
  describe 'save stores the correct data', ->
    it 'saves markdown from markdown editor', ->
      loadFixtures 'problem-with-markdown.html'
      @descriptor = new MarkdownEditingDescriptor($('.problem-editor'))
      saveResult = @descriptor.save()
      expect(saveResult.metadata.markdown).toEqual('markdown')
      expect(saveResult.data).toEqual('<problem>\n<question>\n<p>markdown</p>\n</question>\n</problem>')
    it 'clears markdown when xml editor is selected', ->
      loadFixtures 'problem-with-markdown.html'
      @descriptor = new MarkdownEditingDescriptor($('.problem-editor'))
      @descriptor.createXMLEditor('replace with markdown')
      saveResult = @descriptor.save()
      expect(saveResult.nullout).toEqual(['markdown'])
      expect(saveResult.data).toEqual('replace with markdown')
    it 'saves xml from the xml editor', ->
      loadFixtures 'problem-without-markdown.html'
      @descriptor = new MarkdownEditingDescriptor($('.problem-editor'))
      saveResult = @descriptor.save()
      expect(saveResult.nullout).toEqual(['markdown'])
      expect(saveResult.data).toEqual('xml only')

  describe 'advanced editor opens correctly', ->
    it 'click on advanced editor should work', ->
      loadFixtures 'problem-with-markdown.html'
      @descriptor = new MarkdownEditingDescriptor($('.problem-editor'))
      spyOn(@descriptor, 'confirmConversionToXml').and.returnValue(true)
      expect(@descriptor.confirmConversionToXml).not.toHaveBeenCalled()
      e = jasmine.createSpyObj('e', [ 'preventDefault' ])
      @descriptor.onShowXMLButton(e)
      expect(e.preventDefault).toHaveBeenCalled()
      expect(@descriptor.confirmConversionToXml).toHaveBeenCalled()
      expect($('.editor-bar').length).toEqual(0)

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
    it 'recognizes x as a selection if it is first non whitespace and has whitespace with other non-whitespace', ->
      revisedSelection = MarkdownEditingDescriptor.insertMultipleChoice(' x correct\n x \nex post facto\nb x c\nx c\nxxp')
      expect(revisedSelection).toEqual('(x) correct\n( )  x \n( ) ex post facto\n( ) b x c\n(x) c\n( ) xxp\n')
    it 'removes multiple newlines but not last one', ->
      revisedSelection = MarkdownEditingDescriptor.insertMultipleChoice('a\nx b\n\n\nc\n')
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

  describe 'insertHeader', ->
    it 'inserts the template if selection is empty', ->
      revisedSelection = MarkdownEditingDescriptor.insertHeader('')
      expect(revisedSelection).toEqual(MarkdownEditingDescriptor.headerTemplate)
    it 'wraps existing text', ->
      revisedSelection = MarkdownEditingDescriptor.insertHeader('my text')
      expect(revisedSelection).toEqual('my text\n====\n')

  describe 'insertExplanation', ->
    it 'inserts the template if selection is empty', ->
      revisedSelection = MarkdownEditingDescriptor.insertExplanation('')
      expect(revisedSelection).toEqual(MarkdownEditingDescriptor.explanationTemplate)
    it 'wraps existing text', ->
      revisedSelection = MarkdownEditingDescriptor.insertExplanation('my text')
      expect(revisedSelection).toEqual('[explanation]\nmy text\n[explanation]')

  describe 'markdownToXml', ->
    it 'converts raw text to paragraph', ->
      data = MarkdownEditingDescriptor.markdownToXml('foo')
      expect(data).toEqual('<problem>\n<question>\n<p>foo</p>\n</question>\n</problem>')
    # test default templates
    it 'converts numerical response to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""A numerical response problem accepts a line of text input from the student, and evaluates the input for correctness based on its numerical value.

        The answer is correct if it is within a specified numerical tolerance of the expected answer.

        Enter the numerical value of Pi:
        = 3.14159 +- .02
        [Explanation]
        Pi, or the the ratio between a circle's circumference to its diameter, is an irrational number known to extreme precision. It is value is approximately equal to 3.14.
        [Explanation]
        ---

        Enter the approximate value of 502*9:
        = 502*9 +- 15%
        [Explanation]
        Although you can get an exact value by typing 502*9 into a calculator, the result will be close to 500*10, or 5,000. The grader accepts any response within 15% of the true value, 4518, so that you can use any estimation technique that you like.
        [Explanation]
        ---

        Enter the number of fingers on a human hand:
        = 5
        [Explanation]
        If you look at your hand, you can count that you have five fingers.
        [Explanation]
        ---

        Range tolerance case
        = [6, 7]
        = (1, 2)

        ---

        If first and last symbols are not brackets, or they are not closed, stringresponse will appear.
        = (7), 7
        = (1+2

        """)
      expect(data).toXMLEqual("""<problem>
        <question>
        <p>A numerical response problem accepts a line of text input from the student, and evaluates the input for correctness based on its numerical value.</p>

        <p>The answer is correct if it is within a specified numerical tolerance of the expected answer.</p>

        <p>Enter the numerical value of Pi:</p>
        <numericalresponse answer="3.14159">
          <responseparam type="tolerance" default=".02" />
          <formulaequationinput />
        </numericalresponse>
        <solution>
        <div class="detailed-solution">
        <p>Explanation</p>

        <p>Pi, or the the ratio between a circle's circumference to its diameter, is an irrational number known to extreme precision. It is value is approximately equal to 3.14.</p>

        </div>
        </solution>

        </question>

        <question>


        <p>Enter the approximate value of 502*9:</p>
        <numericalresponse answer="502*9">
          <responseparam type="tolerance" default="15%" />
          <formulaequationinput />
        </numericalresponse>

        <solution>
        <div class="detailed-solution">
        <p>Explanation</p>

        <p>Although you can get an exact value by typing 502*9 into a calculator, the result will be close to 500*10, or 5,000. The grader accepts any response within 15% of the true value, 4518, so that you can use any estimation technique that you like.</p>

        </div>
        </solution>

        </question>

        <question>


        <p>Enter the number of fingers on a human hand:</p>
        <numericalresponse answer="5">
          <formulaequationinput />
        </numericalresponse>

        <solution>
        <div class="detailed-solution">
        <p>Explanation</p>

        <p>If you look at your hand, you can count that you have five fingers.</p>

        </div>
        </solution>

        </question>

        <question>


        <p>Range tolerance case</p>
        <numericalresponse answer="[6, 7]">
          <formulaequationinput />
        </numericalresponse>
        <numericalresponse answer="(1, 2)">
          <formulaequationinput />
        </numericalresponse>


        </question>

        <question>


        <p>If first and last symbols are not brackets, or they are not closed, stringresponse will appear.</p>
        <stringresponse answer="(7), 7" type="ci" >
          <textline size="20"/>
        </stringresponse>
        <stringresponse answer="(1+2" type="ci" >
          <textline size="20"/>
        </stringresponse>
        </question>
        </problem>""")
    it 'will convert 0 as a numerical response (instead of string response)', ->
      data =  MarkdownEditingDescriptor.markdownToXml("""
        Enter 0 with a tolerance:
        = 0 +- .02
        """)
      expect(data).toXMLEqual("""<problem>
        <question>
        <p>Enter 0 with a tolerance:</p>
        <numericalresponse answer="0">
          <responseparam type="tolerance" default=".02" />
          <formulaequationinput />
        </numericalresponse>
        </question>
        </problem>""")
    it 'markup with multiple answers doesn\'t break numerical response', ->
      data =  MarkdownEditingDescriptor.markdownToXml("""
        Enter 1 with a tolerance:
        = 1 +- .02
        or= 2 +- 5%
        """)
      expect(data).toXMLEqual("""<problem>
        <question>
        <p>Enter 1 with a tolerance:</p>
        <numericalresponse answer="1">
          <responseparam type="tolerance" default=".02" />
          <formulaequationinput />
        </numericalresponse>
        </question>
        </problem>""")
    it 'converts multiple choice to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""A multiple choice problem presents radio buttons for student input. Students can only select a single option presented. Multiple Choice questions have been the subject of many areas of research due to the early invention and adoption of bubble sheets.

        One of the main elements that goes into a good multiple choice question is the existence of good distractors. That is, each of the alternate responses presented to the student should be the result of a plausible mistake that a student might make.

        What Apple device competed with the portable CD player?
        ( ) The iPad
        ( ) Napster
        (x) The iPod
        ( ) The vegetable peeler
        ( ) Android
        ( ) The Beatles

        [Explanation]
        The release of the iPod allowed consumers to carry their entire music library with them in a format that did not rely on fragile and energy-intensive spinning disks.
        [Explanation]
        """)
      expect(data).toXMLEqual("""<problem>
        <question>
        <p>A multiple choice problem presents radio buttons for student input. Students can only select a single option presented. Multiple Choice questions have been the subject of many areas of research due to the early invention and adoption of bubble sheets.</p>

        <p>One of the main elements that goes into a good multiple choice question is the existence of good distractors. That is, each of the alternate responses presented to the student should be the result of a plausible mistake that a student might make.</p>

        <p>What Apple device competed with the portable CD player?</p>
        <multiplechoiceresponse>
          <choicegroup type="MultipleChoice">
            <choice correct="false">The iPad</choice>
            <choice correct="false">Napster</choice>
            <choice correct="true">The iPod</choice>
            <choice correct="false">The vegetable peeler</choice>
            <choice correct="false">Android</choice>
            <choice correct="false">The Beatles</choice>
          </choicegroup>
        </multiplechoiceresponse>

        <solution>
        <div class="detailed-solution">
        <p>Explanation</p>

        <p>The release of the iPod allowed consumers to carry their entire music library with them in a format that did not rely on fragile and energy-intensive spinning disks.</p>

        </div>
        </solution>
        </question>
        </problem>""")
    it 'converts multiple choice shuffle to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""A multiple choice problem presents radio buttons for student input. Students can only select a single option presented. Multiple Choice questions have been the subject of many areas of research due to the early invention and adoption of bubble sheets.

        One of the main elements that goes into a good multiple choice question is the existence of good distractors. That is, each of the alternate responses presented to the student should be the result of a plausible mistake that a student might make.

        What Apple device competed with the portable CD player?
        (!x@) The iPad
        (@) Napster
        () The iPod
        ( ) The vegetable peeler
        ( ) Android
        (@) The Beatles

        [Explanation]
        The release of the iPod allowed consumers to carry their entire music library with them in a format that did not rely on fragile and energy-intensive spinning disks.
        [Explanation]
        """)
      expect(data).toXMLEqual("""<problem>
        <question>
        <p>A multiple choice problem presents radio buttons for student input. Students can only select a single option presented. Multiple Choice questions have been the subject of many areas of research due to the early invention and adoption of bubble sheets.</p>

        <p>One of the main elements that goes into a good multiple choice question is the existence of good distractors. That is, each of the alternate responses presented to the student should be the result of a plausible mistake that a student might make.</p>

        <p>What Apple device competed with the portable CD player?</p>
        <multiplechoiceresponse>
          <choicegroup type="MultipleChoice" shuffle="true">
            <choice correct="true" fixed="true">The iPad</choice>
            <choice correct="false" fixed="true">Napster</choice>
            <choice correct="false">The iPod</choice>
            <choice correct="false">The vegetable peeler</choice>
            <choice correct="false">Android</choice>
            <choice correct="false" fixed="true">The Beatles</choice>
          </choicegroup>
        </multiplechoiceresponse>

        <solution>
        <div class="detailed-solution">
        <p>Explanation</p>

        <p>The release of the iPod allowed consumers to carry their entire music library with them in a format that did not rely on fragile and energy-intensive spinning disks.</p>

        </div>
        </solution>
        </question>
        </problem>""")

    it 'converts a series of multiplechoice to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""bleh
        (!x) a
        () b
        () c
        ---
        yatta
        ( ) x
        ( ) y
        (x) z
        ---
        testa
        (!) i
        ( ) ii
        (x) iii
        [Explanation]
        When the student is ready, the explanation appears.
        [Explanation]
        """)
      expect(data).toXMLEqual("""<problem>
        <question>
        <p>bleh</p>
        <multiplechoiceresponse>
          <choicegroup type="MultipleChoice" shuffle="true">
            <choice correct="true">a</choice>
            <choice correct="false">b</choice>
            <choice correct="false">c</choice>
          </choicegroup>
        </multiplechoiceresponse>
        </question>

        <question>
        <p>yatta</p>
        <multiplechoiceresponse>
          <choicegroup type="MultipleChoice">
            <choice correct="false">x</choice>
            <choice correct="false">y</choice>
            <choice correct="true">z</choice>
          </choicegroup>
        </multiplechoiceresponse>
        </question>

        <question>
        <p>testa</p>
        <multiplechoiceresponse>
          <choicegroup type="MultipleChoice" shuffle="true">
            <choice correct="false">i</choice>
            <choice correct="false">ii</choice>
            <choice correct="true">iii</choice>
          </choicegroup>
        </multiplechoiceresponse>

        <solution>
        <div class="detailed-solution">
        <p>Explanation</p>

        <p>When the student is ready, the explanation appears.</p>

        </div>
        </solution>
        </question>
        </problem>""")

    it 'converts OptionResponse to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""OptionResponse gives a limited set of options for students to respond with, and presents those options in a format that encourages them to search for a specific answer rather than being immediately presented with options from which to recognize the correct answer.

        The answer options and the identification of the correct answer is defined in the <b>optioninput</b> tag.

        Translation between Option Response and __________ is extremely straightforward:
        [[(Multiple Choice), String Response, Numerical Response, External Response, Image Response]]

        [Explanation]
        Multiple Choice also allows students to select from a variety of pre-written responses, although the format makes it easier for students to read very long response options. Optionresponse also differs slightly because students are more likely to think of an answer and then search for it rather than relying purely on recognition to answer the question.
        [Explanation]
        """)
      expect(data).toXMLEqual("""<problem>
        <question>
        <p>OptionResponse gives a limited set of options for students to respond with, and presents those options in a format that encourages them to search for a specific answer rather than being immediately presented with options from which to recognize the correct answer.</p>

        <p>The answer options and the identification of the correct answer is defined in the <b>optioninput</b> tag.</p>

        <p>Translation between Option Response and __________ is extremely straightforward:</p>

        <optionresponse>
          <optioninput options="('Multiple Choice','String Response','Numerical Response','External Response','Image Response')" correct="Multiple Choice"></optioninput>
        </optionresponse>

        <solution>
        <div class="detailed-solution">
        <p>Explanation</p>

        <p>Multiple Choice also allows students to select from a variety of pre-written responses, although the format makes it easier for students to read very long response options. Optionresponse also differs slightly because students are more likely to think of an answer and then search for it rather than relying purely on recognition to answer the question.</p>

        </div>
        </solution>
        </question>
        </problem>""")
    it 'converts StringResponse to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""A string response problem accepts a line of text input from the student, and evaluates the input for correctness based on an expected answer within each input box.

        The answer is correct if it matches every character of the expected answer. This can be a problem with international spelling, dates, or anything where the format of the answer is not clear.

        Which US state has Lansing as its capital?
        = Michigan

        [Explanation]
        Lansing is the capital of Michigan, although it is not Michgan's largest city, or even the seat of the county in which it resides.
        [Explanation]
        """)
      expect(data).toXMLEqual("""<problem>
        <question>
        <p>A string response problem accepts a line of text input from the student, and evaluates the input for correctness based on an expected answer within each input box.</p>

        <p>The answer is correct if it matches every character of the expected answer. This can be a problem with international spelling, dates, or anything where the format of the answer is not clear.</p>

        <p>Which US state has Lansing as its capital?</p>
        <stringresponse answer="Michigan" type="ci" >
          <textline size="20"/>
        </stringresponse>

        <solution>
        <div class="detailed-solution">
        <p>Explanation</p>

        <p>Lansing is the capital of Michigan, although it is not Michgan's largest city, or even the seat of the county in which it resides.</p>

        </div>
        </solution>
        </question>
        </problem>""")
    it 'converts StringResponse with regular expression to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""Who lead the civil right movement in the United States of America?
        = | \w*\.?\s*Luther King\s*.*

        [Explanation]
        Test Explanation.
        [Explanation]
        """)
      expect(data).toXMLEqual("""<problem>
        <question>
        <p>Who lead the civil right movement in the United States of America?</p>
        <stringresponse answer="\w*\.?\s*Luther King\s*.*" type="ci regexp" >
          <textline size="20"/>
        </stringresponse>

        <solution>
        <div class="detailed-solution">
        <p>Explanation</p>

        <p>Test Explanation.</p>

        </div>
        </solution>
        </question>
        </problem>""")
    it 'converts StringResponse with multiple answers to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""Who lead the civil right movement in the United States of America?
        = Dr. Martin Luther King Jr.
        or= Doctor Martin Luther King Junior
        or= Martin Luther King
        or= Martin Luther King Junior

        [Explanation]
        Test Explanation.
        [Explanation]
        """)
      expect(data).toXMLEqual("""<problem>
        <question>
        <p>Who lead the civil right movement in the United States of America?</p>
        <stringresponse answer="Dr. Martin Luther King Jr." type="ci" >
          <additional_answer answer="Doctor Martin Luther King Junior"></additional_answer>
          <additional_answer answer="Martin Luther King"></additional_answer>
          <additional_answer answer="Martin Luther King Junior"></additional_answer>
          <textline size="20"/>
        </stringresponse>

        <solution>
        <div class="detailed-solution">
        <p>Explanation</p>

        <p>Test Explanation.</p>

        </div>
        </solution>
        </question>
        </problem>""")
    it 'converts StringResponse with multiple answers and regular expressions to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""Write a number from 1 to 4.
        =| ^One$
        or= two
        or= ^thre+
        or= ^4|Four$

        [Explanation]
        Test Explanation.
        [Explanation]
        """)
      expect(data).toXMLEqual("""<problem>
        <question>
        <p>Write a number from 1 to 4.</p>
        <stringresponse answer="^One$" type="ci regexp" >
          <additional_answer answer="two"></additional_answer>
          <additional_answer answer="^thre+"></additional_answer>
          <additional_answer answer="^4|Four$"></additional_answer>
          <textline size="20"/>
        </stringresponse>

        <solution>
        <div class="detailed-solution">
        <p>Explanation</p>

        <p>Test Explanation.</p>

        </div>
        </solution>
        </question>
        </problem>""")
    # test labels
    it 'converts markdown labels to label attributes', ->
      data = MarkdownEditingDescriptor.markdownToXml(""">>Who lead the civil right movement in the United States of America?<<
        = | \w*\.?\s*Luther King\s*.*

        [Explanation]
        Test Explanation.
        [Explanation]
        """)
      expect(data).toXMLEqual("""<problem>
      <question>
    <p>Who lead the civil right movement in the United States of America?</p>
    <stringresponse answer="w*.?s*Luther Kings*.*" type="ci regexp" >
      <textline label="Who lead the civil right movement in the United States of America?" size="20"/>
    </stringresponse>

    <solution>
    <div class="detailed-solution">
    <p>Explanation</p>

    <p>Test Explanation.</p>

    </div>
    </solution>
    </question>
    </problem>""")
    it 'handles multiple questions with labels', ->
      data = MarkdownEditingDescriptor.markdownToXml("""
        France is a country in Europe.

        >>What is the capital of France?<<
        = Paris
        ---
        Germany is a country in Europe, too.

        >>What is the capital of Germany?<<
        ( ) Bonn
        ( ) Hamburg
        (x) Berlin
        ( ) Donut
      """)
      expect(data).toXMLEqual("""<problem>
      <question>
    <p>France is a country in Europe.</p>

    <p>What is the capital of France?</p>
    <stringresponse answer="Paris" type="ci" >
      <textline label="What is the capital of France?" size="20"/>
    </stringresponse>
    </question>

    <question>
    <p>Germany is a country in Europe, too.</p>

    <p>What is the capital of Germany?</p>
    <multiplechoiceresponse>
      <choicegroup label="What is the capital of Germany?" type="MultipleChoice">
        <choice correct="false">Bonn</choice>
        <choice correct="false">Hamburg</choice>
        <choice correct="true">Berlin</choice>
        <choice correct="false">Donut</choice>
      </choicegroup>
    </multiplechoiceresponse>

    </question>
    </problem>""")
    it 'tests multiple questions with only one label', ->
      data = MarkdownEditingDescriptor.markdownToXml("""
        France is a country in Europe.

        >>What is the capital of France?<<
        = Paris
        ---
        Germany is a country in Europe, too.

        What is the capital of Germany?
        ( ) Bonn
        ( ) Hamburg
        (x) Berlin
        ( ) Donut
        """)
      expect(data).toXMLEqual("""<problem>
      <question>
    <p>France is a country in Europe.</p>

    <p>What is the capital of France?</p>
    <stringresponse answer="Paris" type="ci" >
      <textline label="What is the capital of France?" size="20"/>
    </stringresponse>
    </question>

    <question>
    <p>Germany is a country in Europe, too.</p>

    <p>What is the capital of Germany?</p>
    <multiplechoiceresponse>
      <choicegroup type="MultipleChoice">
        <choice correct="false">Bonn</choice>
        <choice correct="false">Hamburg</choice>
        <choice correct="true">Berlin</choice>
        <choice correct="false">Donut</choice>
      </choicegroup>
    </multiplechoiceresponse>

    </question>
    </problem>""")
    it 'tests malformed labels', ->
      data = MarkdownEditingDescriptor.markdownToXml("""
        France is a country in Europe.

        >>What is the capital of France?<
        = Paris
        ---
        blah>>What is the capital of <<Germany?<<
        ( ) Bonn
        ( ) Hamburg
        (x) Berlin
        ( ) Donut
      """)
      expect(data).toXMLEqual("""<problem>
      <question>
    <p>France is a country in Europe.</p>

    <p>>>What is the capital of France?<</p>
    <stringresponse answer="Paris" type="ci" >
      <textline size="20"/>
    </stringresponse>
    </question>

    <question>
    <p>blahWhat is the capital of Germany?</p>
    <multiplechoiceresponse>
      <choicegroup label="What is the capital of &lt;&lt;Germany?" type="MultipleChoice">
        <choice correct="false">Bonn</choice>
        <choice correct="false">Hamburg</choice>
        <choice correct="true">Berlin</choice>
        <choice correct="false">Donut</choice>
      </choicegroup>
    </multiplechoiceresponse>

    </question>
    </problem>""")
    it 'adds labels to formulae', ->
      data = MarkdownEditingDescriptor.markdownToXml("""
      >>Enter the numerical value of Pi:<<
      = 3.14159 +- .02
      """)
      expect(data).toXMLEqual("""<problem>
      <question>
    <p>Enter the numerical value of Pi:</p>
    <numericalresponse answer="3.14159">
      <responseparam type="tolerance" default=".02" />
      <formulaequationinput label="Enter the numerical value of Pi:" />
    </numericalresponse>

    </question>
    </problem>""")
    it 'escapes entities in labels', ->
      data = MarkdownEditingDescriptor.markdownToXml("""
      >>What is the "capital" of France & the 'best' > place < to live"?<<
      = Paris
      """)
      expect(data).toXMLEqual("""<problem>
      <question>
    <p>What is the "capital" of France & the 'best' > place < to live"?</p>
    <stringresponse answer="Paris" type="ci" >
      <textline label="What is the &quot;capital&quot; of France &amp; the &apos;best&apos; &gt; place &lt; to live&quot;?" size="20"/>
    </stringresponse>

    </question>
    </problem>""")
    # test oddities
    it 'converts headers and oddities to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""Not a header
        A header
        ==============

        Multiple choice w/ parentheticals
        ( ) option (with parens)
        ( ) xd option (x)
        ()) parentheses inside
        () no space b4 close paren

        Choice checks
        [ ] option1 [x]
        [x] correct
        [x] redundant
        [(] distractor
        [] no space

        Option with multiple correct ones
        [[one option, (correct one), (should not be correct)]]

        Option with embedded parens
        [[My (heart), another, (correct)]]

        What happens w/ empty correct options?
        [[()]]

        [Explanation]see[/expLanation]

        [explanation]
        orphaned start

        No p tags in the below
        <script type='javascript'>
           var two = 2;

           console.log(two * 2);
        </script>

        But in this there should be
        <div>
        Great ideas require offsetting.

        bad tests require drivel
        </div>

        [code]
        Code should be nicely monospaced.
        [/code]
        """)
      expect(data).toXMLEqual("""<problem>
        <question>
        <p>Not a header</p>
        <h3 class="hd hd-2 problem-header">A header</h3>

        <p>Multiple choice w/ parentheticals</p>
        <multiplechoiceresponse>
          <choicegroup type="MultipleChoice">
            <choice correct="false">option (with parens)</choice>
            <choice correct="false">xd option (x)</choice>
            <choice correct="false">parentheses inside</choice>
            <choice correct="false">no space b4 close paren</choice>
          </choicegroup>
        </multiplechoiceresponse>

        <p>Choice checks</p>
        <choiceresponse>
          <checkboxgroup>
            <choice correct="false">option1 [x]</choice>
            <choice correct="true">correct</choice>
            <choice correct="true">redundant</choice>
            <choice correct="false">distractor</choice>
            <choice correct="false">no space</choice>
          </checkboxgroup>
        </choiceresponse>

        <p>Option with multiple correct ones</p>

        <optionresponse>
          <optioninput options="('one option','correct one','should not be correct')" correct="correct one"></optioninput>
        </optionresponse>

        <p>Option with embedded parens</p>

        <optionresponse>
          <optioninput options="('My (heart)','another','correct')" correct="correct"></optioninput>
        </optionresponse>

        <p>What happens w/ empty correct options?</p>

        <optionresponse>
          <optioninput options="('')" correct=""></optioninput>
        </optionresponse>

        <solution>
        <div class="detailed-solution">
        <p>Explanation</p>

        <p>see</p>
        </div>
        </solution>

        <p>[explanation]</p>
        <p>orphaned start</p>

        <p>No p tags in the below</p>
        <script type='javascript'>
           var two = 2;

           console.log(two * 2);
        </script>

        <p>But in this there should be</p>
        <div>
        <p>Great ideas require offsetting.</p>

        <p>bad tests require drivel</p>
        </div>

        <pre><code>
        Code should be nicely monospaced.
        </code></pre>
        </question>
        </problem>""")
    # failure tests
