
#
# The pattern below provides a useful mechanism to test the conversion of markdown to XML
# with some resilience built in to account for the fact that whitespace is ignored in both
# markdown and XML. To use this pattern, just make a copy of the 8 lines of pattern code,
# uncomment those 8 lines, and replace three keyword markers with strings appropriate to the
# test you want to construct:
#
#   DESCRIPTION         -- a brief description of the main element(s) begin exercised by this test
#   MARKDOWN_STRING     -- the markdown text which would be created in the simple editor
#   EXPECTED_XML_STRING -- the resulting XML string which *should* be produced when the markdown is translated
#
# There are a several string replacement steps here that may not be obvious:
#
#   1) The single-quote character (') causes some problems when it appears as an apostrophe in the markdown
#      text so the first replacement turns any such characters into a safer back-tick (`) character.
#
#   2) Then, all whitespace (carriage returns, tabs, linefeeds, spaces) are replaced by single spaces. That is,
#      any run of 1 or more of these characters is replaced by a single space.
#
#   3) Any spaces at the beginning of the string is removed via the trim() function.
#
# All transforms are carried out on both the markdown string and the XML resulting string so that a simple
# string comparison should match without regard to whitespace in either of the strings.
#
#      #____________________________________________________________________
#      it 'DESCRIPTION', ->
#                  data = MarkdownEditingDescriptor.markdownToXml("""
#                        MARKDOWN_STRING
#                  """).replace(/'/gm, '`').replace(/\s+/gm, ' ').trim().trim()
#                  expect(data).toEqual(("""
#                        EXPECTED_XML_STRING
#                  """).replace(/'/gm, '`').replace(/\s+/gm, ' ').trim().trim())
#
#

describe 'MarkdownEditingDescriptor', ->
  describe 'save stores the correct data', ->
    it 'saves markdown from markdown editor', ->
      loadFixtures 'problem-with-markdown.html'
      @descriptor = new MarkdownEditingDescriptor($('.problem-editor'))
      saveResult = @descriptor.save()
      expect(saveResult.metadata.markdown).toEqual('markdown')
      expect(saveResult.data).toEqual('<problem>\n<p>markdown</p>\n</problem>')
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
      spyOn(@descriptor, 'confirmConversionToXml').andReturn(true)
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
      expect(data).toEqual('<problem>\n<p>foo</p>\n</problem>')
    # test default templates
    it 'converts numerical response to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""A numerical response problem accepts a line of text input from the student, and evaluates the input for correctness based on its numerical value.

        The answer is correct if it is within a specified numerical tolerance of the expected answer.

        Enter the numerical value of Pi:
        = 3.14159 +- .02

        Enter the approximate value of 502*9:
        = 502*9 +- 15%

        Enter the number of fingers on a human hand:
        = 5

        Range tolerance case
        = [6, 7]
        = (1, 2)

        If first and last symbols are not brackets, or they are not closed, stringresponse will appear, case 1.
        = (7), 7

        If first and last symbols are not brackets, or they are not closed, stringresponse will appear, case 2.
        = (1+2

        [Explanation]
        Pi, or the the ratio between a circle's circumference to its diameter, is an irrational number known to extreme precision. It is value is approximately equal to 3.14.

        Although you can get an exact value by typing 502*9 into a calculator, the result will be close to 500*10, or 5,000. The grader accepts any response within 15% of the true value, 4518, so that you can use any estimation technique that you like.

        If you look at your hand, you can count that you have five fingers.
        [Explanation]
        """)
      expect(data).toEqual("""<problem>
        <p>A numerical response problem accepts a line of text input from the student, and evaluates the input for correctness based on its numerical value.</p>
        <p>The answer is correct if it is within a specified numerical tolerance of the expected answer.</p>
        <p>Enter the numerical value of Pi:</p>
        <numericalresponse answer="3.14159">
          <responseparam type="tolerance" default=".02" />
          <formulaequationinput />
        </numericalresponse>
        <p>Enter the approximate value of 502*9:</p>
        <numericalresponse answer="502*9">
          <responseparam type="tolerance" default="15%" />
          <formulaequationinput />
        </numericalresponse>
        <p>Enter the number of fingers on a human hand:</p>
        <numericalresponse answer="5">
          <formulaequationinput />
        </numericalresponse>
        <p>Range tolerance case</p>
        <numericalresponse answer="[6, 7]">
          <formulaequationinput />
        </numericalresponse>
        <numericalresponse answer="(1, 2)">
          <formulaequationinput />
        </numericalresponse>
        <p>If first and last symbols are not brackets, or they are not closed, stringresponse will appear, case 1.</p>
        <stringresponse answer="(7), 7" type="ci" >
          <textline size="20"/>
        </stringresponse>
        <p>If first and last symbols are not brackets, or they are not closed, stringresponse will appear, case 2.</p>
        <stringresponse answer="(1+2" type="ci" >
          <textline size="20"/>
        </stringresponse>
        <solution>
        <div class="detailed-solution">
        <p>Explanation</p>
        <p>Pi, or the the ratio between a circle's circumference to its diameter, is an irrational number known to extreme precision. It is value is approximately equal to 3.14.</p>
        <p>Although you can get an exact value by typing 502*9 into a calculator, the result will be close to 500*10, or 5,000. The grader accepts any response within 15% of the true value, 4518, so that you can use any estimation technique that you like.</p>
        <p>If you look at your hand, you can count that you have five fingers.</p>

        </div>
        </solution>
        </problem>""")
    it 'will convert 0 as a numerical response (instead of string response)', ->
      data =  MarkdownEditingDescriptor.markdownToXml("""
        Enter 0 with a tolerance:
        = 0 +- .02
        """)
      expect(data).toEqual("""<problem>
        <p>Enter 0 with a tolerance:</p>
        <numericalresponse answer="0">
          <responseparam type="tolerance" default=".02" />
          <formulaequationinput />
        </numericalresponse>
        </problem>""")
    it 'markup with multiple answers doesn\'t break numerical response', ->
      data =  MarkdownEditingDescriptor.markdownToXml("""
        Enter 1 with a tolerance:
        = 1 +- .02
        or= 2 +- 5%
        """)
      expect(data).toEqual("""<problem>
        <p>Enter 1 with a tolerance:</p>
        <numericalresponse answer="1">
          <responseparam type="tolerance" default=".02" />
          <formulaequationinput />
        </numericalresponse>

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
      expect(data).toEqual("""<problem>
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
      expect(data).toEqual("""<problem>
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
        </problem>""")

    it 'converts a series of multiplechoice to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""bleh
        (!x) a
        () b
        () c
        yatta
        ( ) x
        ( ) y
        (x) z
        testa
        (!) i
        ( ) ii
        (x) iii
        [Explanation]
        When the student is ready, the explanation appears.
        [Explanation]
        """)
      expect(data).toEqual("""<problem>
        <p>bleh</p>
        <multiplechoiceresponse>
          <choicegroup type="MultipleChoice" shuffle="true">
            <choice correct="true">a</choice>
            <choice correct="false">b</choice>
            <choice correct="false">c</choice>
          </choicegroup>
        </multiplechoiceresponse>
        <p>yatta</p>
        <multiplechoiceresponse>
          <choicegroup type="MultipleChoice">
            <choice correct="false">x</choice>
            <choice correct="false">y</choice>
            <choice correct="true">z</choice>
          </choicegroup>
        </multiplechoiceresponse>
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
      expect(data).toEqual("""<problem>
        <p>OptionResponse gives a limited set of options for students to respond with, and presents those options in a format that encourages them to search for a specific answer rather than being immediately presented with options from which to recognize the correct answer.</p>
        <p>The answer options and the identification of the correct answer is defined in the <b>optioninput</b> tag.</p>
        <p>Translation between Option Response and __________ is extremely straightforward:</p>
        <optionresponse>
            <optioninput options="(Multiple Choice),String Response,Numerical Response,External Response,Image Response" correct="Multiple Choice">
                  <option  correct="True">Multiple Choice</option>
                  <option  correct="False">String Response</option>
                  <option  correct="False">Numerical Response</option>
                  <option  correct="False">External Response</option>
                  <option  correct="False">Image Response</option>
            </optioninput>
        </optionresponse>

        <solution>
        <div class="detailed-solution">
        <p>Explanation</p>
        <p>Multiple Choice also allows students to select from a variety of pre-written responses, although the format makes it easier for students to read very long response options. Optionresponse also differs slightly because students are more likely to think of an answer and then search for it rather than relying purely on recognition to answer the question.</p>

        </div>
        </solution>
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
      expect(data).toEqual("""<problem>
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
        </problem>""")
    it 'converts StringResponse with regular expression to xml', ->
      data = MarkdownEditingDescriptor.markdownToXml("""Who lead the civil right movement in the United States of America?
        = | \w*\.?\s*Luther King\s*.*

        [Explanation]
        Test Explanation.
        [Explanation]
        """)
      expect(data).toEqual("""<problem>
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
      expect(data).toEqual("""<problem>
        <p>Who lead the civil right movement in the United States of America?</p>
        <stringresponse answer="Dr. Martin Luther King Jr." type="ci" >
          <additional_answer>Doctor Martin Luther King Junior</additional_answer>
          <additional_answer>Martin Luther King</additional_answer>
          <additional_answer>Martin Luther King Junior</additional_answer>
          <textline size="20"/>
        </stringresponse>
        <solution>
        <div class="detailed-solution">
        <p>Explanation</p>
        <p>Test Explanation.</p>

        </div>
        </solution>
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
      expect(data).toEqual("""<problem>
        <p>Write a number from 1 to 4.</p>
        <stringresponse answer="^One$" type="ci regexp" >
          <additional_answer>two</additional_answer>
          <additional_answer>^thre+</additional_answer>
          <additional_answer>^4|Four$</additional_answer>
          <textline size="20"/>
        </stringresponse>
        <solution>
        <div class="detailed-solution">
        <p>Explanation</p>
        <p>Test Explanation.</p>

        </div>
        </solution>
        </problem>""")
    # test labels
    it 'converts markdown labels to label attributes', ->
      data = MarkdownEditingDescriptor.markdownToXml(""">>Who lead the civil right movement in the United States of America?<<
        = | \w*\.?\s*Luther King\s*.*

        [Explanation]
        Test Explanation.
        [Explanation]
        """)
      expect(data).toEqual("""<problem>
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
    </problem>""")
    it 'handles multiple questions with labels', ->
      data = MarkdownEditingDescriptor.markdownToXml("""
        France is a country in Europe.
        >>What is the capital of France?<<
        = Paris
        
        Germany is a country in Europe, too.
        >>What is the capital of Germany?<<
        ( ) Bonn
        ( ) Hamburg
        (x) Berlin
        ( ) Donut
      """)
      expect(data).toEqual("""<problem>
    <p>France is a country in Europe.</p>
    <p>What is the capital of France?</p>
    <stringresponse answer="Paris" type="ci" >
      <textline label="What is the capital of France?" size="20"/>
    </stringresponse>
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
    </problem>""")
    it 'tests multiple questions with only one label', ->
      data = MarkdownEditingDescriptor.markdownToXml("""
        France is a country in Europe.
        >>What is the capital of France?<<
        = Paris

        Germany is a country in Europe, too.

        What is the capital of Germany?
        ( ) Bonn
        ( ) Hamburg
        (x) Berlin
        ( ) Donut
        """)
      expect(data).toEqual("""<problem>
    <p>France is a country in Europe.</p>
    <p>What is the capital of France?</p>
    <stringresponse answer="Paris" type="ci" >
      <textline label="What is the capital of France?" size="20"/>
    </stringresponse>
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
    </problem>""")
    it 'tests malformed labels', ->
      data = MarkdownEditingDescriptor.markdownToXml("""
        France is a country in Europe.
        >>What is the capital of France?<
        = Paris

        blah>>What is the capital of <<Germany?<<
        ( ) Bonn
        ( ) Hamburg
        (x) Berlin
        ( ) Donut
      """)
      expect(data).toEqual("""<problem>
    <p>France is a country in Europe.</p>
    <p>>>What is the capital of France?<</p>
    <stringresponse answer="Paris" type="ci" >
      <textline size="20"/>
    </stringresponse>
    <p>blahWhat is the capital of Germany?</p>
    <multiplechoiceresponse>
      <choicegroup label="What is the capital of &lt;&lt;Germany?" type="MultipleChoice">
        <choice correct="false">Bonn</choice>
        <choice correct="false">Hamburg</choice>
        <choice correct="true">Berlin</choice>
        <choice correct="false">Donut</choice>
      </choicegroup>
    </multiplechoiceresponse>
    </problem>""")
    it 'adds labels to formulae', ->
      data = MarkdownEditingDescriptor.markdownToXml("""
      >>Enter the numerical value of Pi:<<
      = 3.14159 +- .02
      """)
      expect(data).toEqual("""<problem>
    <p>Enter the numerical value of Pi:</p>
    <numericalresponse answer="3.14159">
      <responseparam type="tolerance" default=".02" />
      <formulaequationinput label="Enter the numerical value of Pi:" />
    </numericalresponse>
    </problem>""")
    it 'escapes entities in labels', ->
      data = MarkdownEditingDescriptor.markdownToXml("""
      >>What is the "capital" of France & the 'best' > place < to live"?<<
      = Paris
      """)
      expect(data).toEqual("""<problem>
    <p>What is the "capital" of France & the 'best' > place < to live"?</p>
    <stringresponse answer="Paris" type="ci" >
      <textline label="What is the &quot;capital&quot; of France &amp; the &apos;best&apos; &gt; place &lt; to live&quot;?" size="20"/>
    </stringresponse>
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
      expect(data).toEqual("""<problem>
    <p>Not a header</p>
    <h1>A header</h1>
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
      <checkboxgroup direction="vertical">
        <choice correct="false">option1 [x]</choice>
        <choice correct="true">correct</choice>
        <choice correct="true">redundant</choice>
        <choice correct="false">no space</choice>
      </checkboxgroup>
    </choiceresponse>
    <p>Option with multiple correct ones</p>
    <optionresponse>
        <optioninput options="one option,(correct one),(should not be correct)" correct="correct one">
              <option  correct="False">one option</option>
              <option  correct="True">correct one</option>
              <option  correct="False">(should not be correct)</option>
        </optioninput>
    </optionresponse>
    <p>Option with embedded parens</p>
    <optionresponse>
        <optioninput options="My (heart),another,(correct)" correct="correct">
              <option  correct="False">My (heart)</option>
              <option  correct="False">another</option>
              <option  correct="True">correct</option>
        </optioninput>
    </optionresponse>
    <p>What happens w/ empty correct options?</p>
    <optionresponse>
        <optioninput options="()" correct="">
              <option  correct="False">()</option>
        </optioninput>
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
    </script><p>But in this there should be</p>
    <div>
    <p>Great ideas require offsetting.</p>
    <p>bad tests require drivel</p>
    </div>

    <pre><code>
    Code should be nicely monospaced.
    </code></pre>
    </problem>""")
    # failure tests

    ################################################################ hinting tests

    squashWhitespace = (unsquashedString) ->
      unsquashedString.replace(/'/gm, '`').replace(/\s+/gm, ' ').trim()

    # this helper function provides a way to compare markdown text with the resulting
    # XML, but independent of any differences in whitespace between the two. The
    # comparison process proceeds in 4 steps:
    #     1) the markdown to be parsed is passed to 'markdownToXml'
    #     2) the XML returned by that call has all runs of whitespace squashed down
    #        to a single space
    #     3) the expected XML is squashed in exactly the same way
    #     4) a straight string comparison is done
    verifyMarkdownParsing = (markdownText, expectedXML) ->
      generatedXML = MarkdownEditingDescriptor.markdownToXml(markdownText)
      expect(squashWhitespace(generatedXML)).toEqual(squashWhitespace(expectedXML))


    describe 'hinting tests', ->
      #____________________________________________________________________
      #____________________________________________________________________
      describe 'drop down components', ->
        it 'multiple component drop down', ->
          verifyMarkdownParsing(
            """
                           Translation between Dropdown and ________ is straightforward.

                          [[
                             (Multiple Choice) 	 {{ Good Job::Yes, multiple choice is the right answer. }}
                             Text Input	                  {{ No, text input problems don't present options. }}
                             Numerical Input	 {{ No, numerical input problems don't present options. }}
                          ]]




                        Clowns have funny _________ to make people laugh.
                        [[
                          dogs		{{ NOPE::Not dogs, not cats, not toads }}
                          (FACES)	{{ With lots of makeup, doncha know?}}
                          money       {{ Clowns don't have any money, of course }}
                          donkeys     {{don't be an ass.}}
                          -no hint-
                        ]]

            ""","""
                        <problem>
                        <p>Translation between Dropdown and ________ is straightforward.</p>
                        <optionresponse>
                            <optioninput options="(Multiple Choice),Text Input,Numerical Input" correct="Multiple Choice">
                                  <option  correct="True">Multiple Choice
                                       <optionhint  label="Good Job">Yes, multiple choice is the right answer.
                                       </optionhint>
                        </option>
                                  <option  correct="False">Text Input
                                       <optionhint  >No, text input problems don't present options.
                                       </optionhint>
                        </option>
                                  <option  correct="False">Numerical Input
                                       <optionhint  >No, numerical input problems don't present options.
                                       </optionhint>
                        </option>
                            </optioninput>
                        </optionresponse>
                        <p>Clowns have funny _________ to make people laugh.</p>
                        <optionresponse>
                            <optioninput options="dogs,(FACES),money,donkeys,-no hint-" correct="FACES">
                                  <option  correct="False">dogs
                                       <optionhint  label="NOPE">Not dogs, not cats, not toads
                                       </optionhint>
                        </option>
                                  <option  correct="True">FACES
                                       <optionhint  >With lots of makeup, doncha know?
                                       </optionhint>
                        </option>
                                  <option  correct="False">money
                                       <optionhint  >Clowns don't have any money, of course
                                       </optionhint>
                        </option>
                                  <option  correct="False">donkeys
                                       <optionhint  >don't be an ass.
                                       </optionhint>
                        </option>
                                  <option  correct="False">-no hint-</option>
                            </optioninput>
                        </optionresponse>
                        </problem>
            """)

        #____________________________________________________________________
        it 'simple dropdown, including 3 problem hints', ->
          verifyMarkdownParsing(
            """
                           Translation between Dropdown and ________ is straightforward.

                          [[
                             (Multiple Choice) 	 {{ Good Job::Yes, multiple choice is the right answer. }}
                             Text Input	                  {{ No, text input problems do not present options. }}
                             Numerical Input	 {{ No, numerical input problems do not present options. }}
                          ]]

                          || 0) your mother wears army boots. ||
                          || 1) roses are red. ||
                          || 2) violets are blue. ||
            ""","""
                          <problem>
                          <p>Translation between Dropdown and ________ is straightforward.</p>
                          <optionresponse>
                              <optioninput options="(Multiple Choice),Text Input,Numerical Input" correct="Multiple Choice">
                                    <option  correct="True">Multiple Choice
                                         <optionhint  label="Good Job">Yes, multiple choice is the right answer.
                                         </optionhint>
                          </option>
                                    <option  correct="False">Text Input
                                         <optionhint  >No, text input problems do not present options.
                                         </optionhint>
                          </option>
                                    <option  correct="False">Numerical Input
                                         <optionhint  >No, numerical input problems do not present options.
                                         </optionhint>
                          </option>
                              </optioninput>
                          </optionresponse>

                              <demandhint>
                                  <hint>  0) your mother wears army boots.
                                  </hint>
                                  <hint>  1) roses are red.
                                  </hint>
                                  <hint>  2) violets are blue.
                                  </hint>
                              </demandhint>
                          </problem>
            """)

      #____________________________________________________________________
      #____________________________________________________________________
      describe 'checkbox components', ->
        #____________________________________________________________________
        it 'multiple checkbox components', ->
          verifyMarkdownParsing(
            """
                          >>Select all the fruits from the list<<

                                  [x] Apple     	 	 {{ selected: You’re right that apple is a fruit. }, {unselected: Remember that apple is also a fruit.}}
                                  [ ] Mushroom	   	 {{U: You’re right that mushrooms aren’t fruit}, { selected: Mushroom is a fungus, not a fruit.}}
                                  [x] Grape		     {{ selected: You’re right that grape is a fruit }, {unselected: Remember that grape is also a fruit.}}
                                  [ ] Mustang
                                  [ ] Camero            {{S:I don't know what a Camero is but it isn't a fruit.},{U:What is a camero anyway?}}


                                  {{ ((A*B)) You’re right that apple is a fruit, but there’s one you’re missing. Also, mushroom is not a fruit.}}
                                  {{ ((B*C)) You’re right that grape is a fruit, but there’s one you’re missing. Also, mushroom is not a fruit.}}



                           >>Select all the vegetables from the list<<

                                  [ ] Banana     	 	 {{ selected: No, sorry, a banana is a fruit. }, {unselected: poor banana.}}
                                  [ ] Ice Cream
                                  [ ] Mushroom	   	 {{U: You’re right that mushrooms aren’t vegatbles}, { selected: Mushroom is a fungus, not a vegetable.}}
                                  [x] Brussel Sprout	 {{S: Brussel sprouts are vegetables.}, {u: Brussel sprout is the only vegetable in this list.}}


                                  {{ ((A*B)) Making a banana split? }}
                                  {{ ((B*D)) That will make a horrible dessert: a brussel sprout split? }}

            ""","""
                            <problem>
                              <p>Select all the fruits from the list</p>
                              <choiceresponse>
                                <checkboxgroup label="Select all the fruits from the list" direction="vertical">
                                  <choice correct="true">Apple
                                             <choicehint selected="true">You’re right that apple is a fruit.
                                             </choicehint>
                                             <choicehint selected="false">Remember that apple is also a fruit.
                                             </choicehint>
                                  </choice>
                                  <choice correct="false">Mushroom
                                             <choicehint selected="true">Mushroom is a fungus, not a fruit.
                                             </choicehint>
                                             <choicehint selected="false">You’re right that mushrooms aren’t fruit
                                             </choicehint>
                                  </choice>
                                  <choice correct="true">Grape
                                             <choicehint selected="true">You’re right that grape is a fruit
                                             </choicehint>
                                             <choicehint selected="false">Remember that grape is also a fruit.
                                             </choicehint>
                                  </choice>
                                  <choice correct="false">Mustang</choice>
                                  <choice correct="false">Camero
                                             <choicehint selected="true">I don't know what a Camero is but it isn't a fruit.
                                             </choicehint>
                                             <choicehint selected="false">What is a camero anyway?
                                             </choicehint>
                                  </choice>
                                  <booleanhint value="A*B"> You’re right that apple is a fruit, but there’s one you’re missing. Also, mushroom is not a fruit.
                                  </booleanhint>
                                  <booleanhint value="B*C"> You’re right that grape is a fruit, but there’s one you’re missing. Also, mushroom is not a fruit.
                                  </booleanhint>
                                </checkboxgroup>
                              </choiceresponse>
                              <p>Select all the vegetables from the list</p>
                              <choiceresponse>
                                <checkboxgroup label="Select all the vegetables from the list" direction="vertical">
                                  <choice correct="false">Banana
                                             <choicehint selected="true">No, sorry, a banana is a fruit.
                                             </choicehint>
                                             <choicehint selected="false">poor banana.
                                             </choicehint>
                                  </choice>
                                  <choice correct="false">Ice Cream</choice>
                                  <choice correct="false">Mushroom
                                             <choicehint selected="true">Mushroom is a fungus, not a vegetable.
                                             </choicehint>
                                             <choicehint selected="false">You’re right that mushrooms aren’t vegatbles
                                             </choicehint>
                                  </choice>
                                  <choice correct="true">Brussel Sprout
                                             <choicehint selected="true">Brussel sprouts are vegetables.
                                             </choicehint>
                                             <choicehint selected="false">Brussel sprout is the only vegetable in this list.
                                             </choicehint>
                                  </choice>
                                  <booleanhint value="A*B"> Making a banana split?
                                  </booleanhint>
                                  <booleanhint value="B*D"> That will make a horrible dessert: a brussel sprout split?
                                  </booleanhint>
                                </checkboxgroup>
                              </choiceresponse>
                            </problem>
            """)

        #____________________________________________________________________
        it 'multiple checkbox components, including 3 problem hints', ->
          verifyMarkdownParsing(
            """
                          >>Select all the fruits from the list<<

                                  [x] Apple     	 	 {{ selected: You’re right that apple is a fruit. }, {unselected: Remember that apple is also a fruit.}}
                                  [ ] Mushroom	   	 {{U: You’re right that mushrooms aren’t fruit}, { selected: Mushroom is a fungus, not a fruit.}}
                                  [x] Grape		     {{ selected: You’re right that grape is a fruit }, {unselected: Remember that grape is also a fruit.}}
                                  [ ] Mustang
                                  [ ] Camero            {{S:I don't know what a Camero is but it isn't a fruit.},{U:What is a camero anyway?}}


                                  {{ ((A*B)) You’re right that apple is a fruit, but there’s one you’re missing. Also, mushroom is not a fruit.}}
                                  {{ ((B*C)) You’re right that grape is a fruit, but there’s one you’re missing. Also, mushroom is not a fruit.}}



                           >>Select all the vegetables from the list<<

                                  [ ] Banana     	 	 {{ selected: No, sorry, a banana is a fruit. }, {unselected: poor banana.}}
                                  [ ] Ice Cream
                                  [ ] Mushroom	   	 {{U: You’re right that mushrooms aren’t vegatbles}, { selected: Mushroom is a fungus, not a vegetable.}}
                                  [x] Brussel Sprout	 {{S: Brussel sprouts are vegetables.}, {u: Brussel sprout is the only vegetable in this list.}}


                                  {{ ((A*B)) Making a banana split? }}
                                  {{ ((B*D)) That will make a horrible dessert: a brussel sprout split? }}




                          || Hint one.||
                          || Hint two. ||
                          || Hint three. ||
            ""","""
                            <problem>
                            <p>Select all the fruits from the list</p>
                            <choiceresponse>
                              <checkboxgroup label="Select all the fruits from the list" direction="vertical">
                                <choice correct="true">Apple
                                           <choicehint selected="true">You’re right that apple is a fruit.
                                           </choicehint>
                                           <choicehint selected="false">Remember that apple is also a fruit.
                                           </choicehint>
                                </choice>
                                <choice correct="false">Mushroom
                                           <choicehint selected="true">Mushroom is a fungus, not a fruit.
                                           </choicehint>
                                           <choicehint selected="false">You’re right that mushrooms aren’t fruit
                                           </choicehint>
                                </choice>
                                <choice correct="true">Grape
                                           <choicehint selected="true">You’re right that grape is a fruit
                                           </choicehint>
                                           <choicehint selected="false">Remember that grape is also a fruit.
                                           </choicehint>
                                </choice>
                                <choice correct="false">Mustang</choice>
                                <choice correct="false">Camero
                                           <choicehint selected="true">I don't know what a Camero is but it isn't a fruit.
                                           </choicehint>
                                           <choicehint selected="false">What is a camero anyway?
                                           </choicehint>
                                </choice>
                                <booleanhint value="A*B"> You’re right that apple is a fruit, but there’s one you’re missing. Also, mushroom is not a fruit.
                                </booleanhint>
                                <booleanhint value="B*C"> You’re right that grape is a fruit, but there’s one you’re missing. Also, mushroom is not a fruit.
                                </booleanhint>
                              </checkboxgroup>
                            </choiceresponse>
                            <p>Select all the vegetables from the list</p>
                            <choiceresponse>
                              <checkboxgroup label="Select all the vegetables from the list" direction="vertical">
                                <choice correct="false">Banana
                                           <choicehint selected="true">No, sorry, a banana is a fruit.
                                           </choicehint>
                                           <choicehint selected="false">poor banana.
                                           </choicehint>
                                </choice>
                                <choice correct="false">Ice Cream</choice>
                                <choice correct="false">Mushroom
                                           <choicehint selected="true">Mushroom is a fungus, not a vegetable.
                                           </choicehint>
                                           <choicehint selected="false">You’re right that mushrooms aren’t vegatbles
                                           </choicehint>
                                </choice>
                                <choice correct="true">Brussel Sprout
                                           <choicehint selected="true">Brussel sprouts are vegetables.
                                           </choicehint>
                                           <choicehint selected="false">Brussel sprout is the only vegetable in this list.
                                           </choicehint>
                                </choice>
                                <booleanhint value="A*B"> Making a banana split?
                                </booleanhint>
                                <booleanhint value="B*D"> That will make a horrible dessert: a brussel sprout split?
                                </booleanhint>
                              </checkboxgroup>
                            </choiceresponse>
                            <demandhint>
                                <hint>  Hint one.
                                </hint>
                                <hint>  Hint two.
                                </hint>
                                <hint>  Hint three.
                                </hint>
                            </demandhint>
                            </problem>
            """)

      #____________________________________________________________________
      #____________________________________________________________________
      describe 'multiple choice components', ->
        #____________________________________________________________________
        it 'dual multiple choice components ', ->
          verifyMarkdownParsing(
            """
                           >>Select the fruit from the list<<

                                      () Mushroom	  	 {{ Mushroom is a fungus, not a fruit.}}
                                      () Potato
                                     (x) Apple     	 	 {{ OUTSTANDING::Apple is indeed a fruit.}}

                           >>Select the vegetables from the list<<

                                      () Mushroom	  	 {{ Mushroom is a fungus, not a vegetable.}}
                                      (x) Potato	                 {{ Potato is a root vegetable. }}
                                      () Apple     	 	 {{ OOPS::Apple is a fruit.}}

            ""","""
                          <problem>
                              <p>Select the fruit from the list</p>
                              <multiplechoiceresponse>
                                <choicegroup label="Select the fruit from the list" type="MultipleChoice">
                                  <choice correct="false">Mushroom
                                      <choicehint>Mushroom is a fungus, not a fruit.
                                      </choicehint>
                                  </choice>
                                  <choice correct="false">Potato</choice>
                                  <choice correct="true">Apple
                                      <choicehint  label="OUTSTANDING">Apple is indeed a fruit.
                                      </choicehint>
                                  </choice>
                                </choicegroup>
                              </multiplechoiceresponse>
                              <p>Select the vegetables from the list</p>
                              <multiplechoiceresponse>
                                <choicegroup label="Select the vegetables from the list" type="MultipleChoice">
                                  <choice correct="false">Mushroom
                                      <choicehint>Mushroom is a fungus, not a vegetable.
                                      </choicehint>
                                  </choice>
                                  <choice correct="true">Potato
                                      <choicehint>Potato is a root vegetable.
                                      </choicehint>
                                  </choice>
                                  <choice correct="false">Apple
                                      <choicehint  label="OOPS">Apple is a fruit.
                                      </choicehint>
                                  </choice>
                                </choicegroup>
                              </multiplechoiceresponse>
                           </problem>

            """)

        #____________________________________________________________________
        it 'dual multiple choice components, including 2 problem hints ', ->
          verifyMarkdownParsing(
            """

                           >>Select the fruit from the list<<

                                      () Mushroom	  	 {{ Mushroom is a fungus, not a fruit.}}
                                      () Potato
                                     (x) Apple     	 	 {{ OUTSTANDING::Apple is indeed a fruit.}}


                          || 0) your mother wears army boots. ||
                          || 1) roses are red. ||
                           >>Select the vegetables from the list<<

                                      () Mushroom	  	 {{ Mushroom is a fungus, not a vegetable.}}
                                      (x) Potato	                 {{ Potato is a root vegetable. }}
                                      () Apple     	 	 {{ OOPS::Apple is a fruit.}}


                           || 2) where are the lions? ||



            ""","""
                            <problem>
                                <p>Select the fruit from the list</p>
                                <multiplechoiceresponse>
                                    <choicegroup label="Select the fruit from the list" type="MultipleChoice">
                                        <choice correct="false">Mushroom <choicehint>Mushroom is a fungus, not a fruit. </choicehint> </choice>
                                        <choice correct="false">Potato</choice>
                                        <choice correct="true">Apple <choicehint label="OUTSTANDING">Apple is indeed a fruit. </choicehint> </choice>
                                    </choicegroup>
                                </multiplechoiceresponse>
                                <p>Select the vegetables from the list</p>
                                <multiplechoiceresponse>
                                    <choicegroup label="Select the vegetables from the list" type="MultipleChoice">
                                        <choice correct="false">Mushroom <choicehint>Mushroom is a fungus, not a vegetable. </choicehint> </choice>
                                        <choice correct="true">Potato <choicehint>Potato is a root vegetable. </choicehint> </choice>
                                        <choice correct="false">Apple <choicehint label="OOPS">Apple is a fruit. </choicehint> </choice>
                                    </choicegroup>
                                </multiplechoiceresponse>
                                <p> </p>
                                <demandhint>
                                    <hint> 0) your mother wears army boots. </hint>
                                    <hint> 1) roses are red. </hint>
                                    <hint> 2) where are the lions? </hint>
                                </demandhint>
                            </problem>

            """)

      #____________________________________________________________________
      #____________________________________________________________________
      describe 'text input components', ->
        #____________________________________________________________________
        it 'simple single text input component', ->
          verifyMarkdownParsing(
            """
                            >>In which country would you find the city of Paris?<<

                            = France		{{ BRAVO::Viva la France! }}

            ""","""
                            <problem>
                            <p>In which country would you find the city of Paris?</p>
                            <stringresponse answer="France" type="ci" >
                                <correcthint  label="BRAVO">Viva la France!
                                </correcthint>
                              <textline label="In which country would you find the city of Paris?" size="20"/>
                            </stringresponse>

                            </problem>
            """)

        #____________________________________________________________________
        it 'simple single text input component, with problem hints', ->
          verifyMarkdownParsing(
            """
                          >>In which country would you find the city of Paris?<<

                          = France		{{ BRAVO::Viva la France! }}


                          || There are actually two countries with cities named Paris. ||
                          || Paris is the capital of one of those countries. ||

            ""","""
                          <problem>
                          <p>In which country would you find the city of Paris?</p>
                          <stringresponse answer="France" type="ci" >
                              <correcthint  label="BRAVO">Viva la France!
                              </correcthint>
                            <textline label="In which country would you find the city of Paris?" size="20"/>
                          </stringresponse>
                              <demandhint>
                                  <hint>  There are actually two countries with cities named Paris.
                                  </hint>
                                  <hint>  Paris is the capital of one of those countries.
                                  </hint>
                              </demandhint>
                          </problem>

            """)

        #____________________________________________________________________
        it 'text input component, with an alternate correct answer', ->
          verifyMarkdownParsing(
            """
                                >>In which country would you find the city of Paris?<<

                                = France		{{ BRAVO::Viva la France! }}
                            or= USA			{{ There is a town in Texas called Paris.}}

            ""","""
                            <problem>
                            <p>In which country would you find the city of Paris?</p>
                            <stringresponse answer="France" type="ci" >
                                <correcthint  label="BRAVO">Viva la France!
                                </correcthint>
                                <additional_answer  answer="USA">There is a town in Texas called Paris.
                              </additional_answer>
                              <textline label="In which country would you find the city of Paris?" size="20"/>
                            </stringresponse>
                            </problem>
            """)

      #____________________________________________________________________
      #____________________________________________________________________
      describe 'numeric input components', ->
        #____________________________________________________________________
        it 'simple single text input component', ->
          verifyMarkdownParsing(
            """

                            >>Enter the numerical value of Pi:<<
                            = 3.14159 +- .02

                            >>Enter the approximate value of 502*9:<<
                            = 4518 +- 15%

                            >>Enter the number of fingers on a human hand<<
                            = 5

            ""","""
                            <problem>
                            <p>Enter the numerical value of Pi:</p>
                            <numericalresponse answer="3.14159">
                              <responseparam type="tolerance" default=".02" />
                              <formulaequationinput label="Enter the numerical value of Pi:" />
                            </numericalresponse>
                            <p>Enter the approximate value of 502*9:</p>
                            <numericalresponse answer="4518">
                              <responseparam type="tolerance" default="15%" />
                              <formulaequationinput label="Enter the approximate value of 502*9:" />
                            </numericalresponse>
                            <p>Enter the number of fingers on a human hand</p>
                            <numericalresponse answer="5">
                              <formulaequationinput label="Enter the number of fingers on a human hand" />
                            </numericalresponse>
                            </problem>

            """)
